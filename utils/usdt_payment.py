# utils/usdt_payment.py
"""Self-serve USDT (TRC20) checkout. Amount is unique per machine+plan so the
app can match an on-chain transfer without a backend, then issue a license.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from config import (
    APP_NAME,
    APP_VERSION,
    BASE_DIR,
    HIDDEN_LICENSE_DIR,
    REVENUE_PLANS,
    TRONGRID_API_URL,
    USDT_PAYMENT_MAX_AGE_SEC,
    USDT_PAYMENT_NETWORK,
    USDT_TRC20_ADDRESS,
    USDT_TRC20_CONTRACT,
)
from utils.logger import setup_logger

logger = setup_logger("RebarAgent.USDT")

USDT_DECIMALS = 6
MICROS_PER_CENT = 10_000  # 0.01 USDT with 6 on-chain decimals
TRON_ADDRESS_RE = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
PAYMENT_JSON_NAMES = ("payment.json",)

# sku -> signed license type (see utils.license.PLAN_SKU_TO_LICENSE_TYPE)
CHECKOUT_LICENSE_TYPE = {
    "pro_3m": "3month",
    "pro_6m": "6month",
    "pro_1y": "1year",
    "office_1y": "1year",
    "unlimited": "unlimited",
}


@dataclass(frozen=True)
class CheckoutPlan:
    sku: str
    license_type: str
    name_en: str
    name_fa: str
    days: Optional[int]
    price_usd: int
    seats: Optional[int] = None


@dataclass(frozen=True)
class Invoice:
    sku: str
    machine_id: str
    address: str
    network: str
    amount_micros: int
    amount_usdt: str

    @property
    def amount_display(self) -> str:
        return f"{self.amount_usdt} USDT"


@dataclass(frozen=True)
class Transfer:
    txid: str
    to_addr: str
    value_micros: int
    timestamp_ms: int
    contract: str = ""
    symbol: str = ""


def _b58decode(value: str) -> bytes:
    num = 0
    for char in value:
        num = num * 58 + _B58_ALPHABET.index(char)
    combined = num.to_bytes((num.bit_length() + 7) // 8 or 1, "big")
    pad = 0
    for char in value:
        if char != "1":
            break
        pad += 1
    return b"\x00" * pad + combined


def is_valid_tron_address(address: str) -> bool:
    """Length/charset plus base58check (Tron mainnet prefix 0x41)."""
    text = (address or "").strip()
    if not TRON_ADDRESS_RE.match(text):
        return False
    try:
        raw = _b58decode(text)
    except (ValueError, IndexError):
        return False
    if len(raw) < 25:
        raw = raw.rjust(25, b"\x00")
    if len(raw) != 25 or raw[0] != 0x41:
        return False
    payload, checksum = raw[:21], raw[21:]
    digest = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return digest == checksum


def _read_json_address(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(
        data.get("usdt_trc20_address")
        or data.get("address")
        or data.get("USDT_TRC20_ADDRESS")
        or ""
    ).strip()


def get_usdt_receive_address() -> str:
    """Resolve the receive wallet: env, config, then payment.json next to the app."""
    candidates = [
        os.environ.get("REBARAGENT_USDT_TRC20", "").strip(),
        (USDT_TRC20_ADDRESS or "").strip(),
    ]
    for folder in (BASE_DIR, HIDDEN_LICENSE_DIR):
        for name in PAYMENT_JSON_NAMES:
            candidates.append(_read_json_address(os.path.join(folder, name)))
    for addr in candidates:
        if addr:
            return addr
    return ""


def list_checkout_plans() -> List[CheckoutPlan]:
    """Flatten REVENUE_PLANS durations into buyable SKUs (trial excluded)."""
    plans: List[CheckoutPlan] = []
    for code, spec in REVENUE_PLANS.items():
        if code == "trial":
            continue
        durations = spec.get("durations") or {}
        seats = spec.get("seats")
        for sku, dur in durations.items():
            days = dur.get("days")
            price = int(dur.get("price_usd") or 0)
            if price <= 0:
                continue
            plans.append(
                CheckoutPlan(
                    sku=sku,
                    license_type=CHECKOUT_LICENSE_TYPE.get(sku, "1year"),
                    name_en=spec.get("name_en") or code,
                    name_fa=spec.get("name_fa") or code,
                    days=days,
                    price_usd=price,
                    seats=seats,
                )
            )
    order = ["pro_3m", "pro_6m", "pro_1y", "office_1y", "unlimited"]
    rank = {sku: i for i, sku in enumerate(order)}
    plans.sort(key=lambda p: (rank.get(p.sku, 99), p.price_usd))
    return plans


def get_checkout_plan(sku: str) -> Optional[CheckoutPlan]:
    for plan in list_checkout_plans():
        if plan.sku == sku:
            return plan
    return None


def unique_suffix_cents(machine_id: str, sku: str) -> int:
    """Stable 10–99 cents so each machine+plan has a distinct on-chain amount.

    Two-decimal amounts stay paste-friendly in wallets. Collisions between
    different machines on the same SKU are possible (~1/90); acceptable at
    low volume because there is no shared backend.
    """
    digest = hashlib.sha256(f"{machine_id}|{sku}".encode("utf-8")).digest()
    return 10 + (int.from_bytes(digest[:2], "big") % 90)


def expected_amount_micros(sku: str, machine_id: str) -> int:
    plan = get_checkout_plan(sku)
    if plan is None:
        raise ValueError(f"Unknown checkout SKU: {sku}")
    base_cents = int(plan.price_usd) * 100
    total_cents = base_cents + unique_suffix_cents(machine_id, sku)
    return total_cents * MICROS_PER_CENT


def format_usdt(amount_micros: int) -> str:
    return f"{amount_micros / (10 ** USDT_DECIMALS):.2f}"


def build_invoice(sku: str, machine_id: str, address: Optional[str] = None) -> Invoice:
    addr = (address if address is not None else get_usdt_receive_address()).strip()
    micros = expected_amount_micros(sku, machine_id)
    return Invoice(
        sku=sku,
        machine_id=machine_id,
        address=addr,
        network=USDT_PAYMENT_NETWORK,
        amount_micros=micros,
        amount_usdt=format_usdt(micros),
    )


def _used_tx_path() -> str:
    return os.path.join(HIDDEN_LICENSE_DIR, "used_usdt_txids.json")


def load_used_txids(path: Optional[str] = None) -> List[str]:
    target = path or _used_tx_path()
    try:
        with open(target, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return [str(x) for x in data]
        if isinstance(data, dict):
            return [str(x) for x in data.get("txids", [])]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def remember_txid(txid: str, path: Optional[str] = None) -> None:
    target = path or _used_tx_path()
    used = load_used_txids(target)
    if txid in used:
        return
    used.append(txid)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        json.dump({"txids": used}, fh, indent=2)


def parse_trc20_transfers(payload: Dict) -> List[Transfer]:
    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    out: List[Transfer] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        token = row.get("token_info") or {}
        contract = str(token.get("address") or row.get("contract_address") or "")
        try:
            value = int(str(row.get("value") or "0"))
        except (TypeError, ValueError):
            continue
        try:
            ts = int(row.get("block_timestamp") or row.get("timestamp") or 0)
        except (TypeError, ValueError):
            ts = 0
        out.append(
            Transfer(
                txid=str(row.get("transaction_id") or row.get("txID") or ""),
                to_addr=str(row.get("to") or ""),
                value_micros=value,
                timestamp_ms=ts,
                contract=contract,
                symbol=str(token.get("symbol") or ""),
            )
        )
    return out


def match_payment(
    transfers: Iterable[Transfer],
    *,
    address: str,
    amount_micros: int,
    now_ms: int,
    max_age_sec: int = USDT_PAYMENT_MAX_AGE_SEC,
    used_txids: Optional[Iterable[str]] = None,
    txid: Optional[str] = None,
) -> Optional[Transfer]:
    """Return the first incoming USDT transfer that matches this invoice."""
    used = set(used_txids or ())
    max_age_ms = max_age_sec * 1000
    want_addr = address.strip()
    want_tx = (txid or "").strip()
    for tx in transfers:
        if not tx.txid:
            continue
        if want_tx and tx.txid != want_tx:
            continue
        if tx.txid in used:
            continue
        if tx.to_addr != want_addr:
            continue
        if tx.contract and tx.contract != USDT_TRC20_CONTRACT:
            continue
        if tx.symbol and tx.symbol.upper() not in ("USDT", ""):
            continue
        if tx.value_micros != amount_micros:
            continue
        if tx.timestamp_ms <= 0:
            continue
        age = now_ms - tx.timestamp_ms
        if age < 0 or age > max_age_ms:
            continue
        return tx
    return None


def fetch_incoming_usdt(
    address: str,
    *,
    limit: int = 80,
    timeout: int = 20,
    opener=None,
) -> List[Transfer]:
    if not is_valid_tron_address(address):
        raise ValueError("Invalid TRON receive address")
    url = (
        f"{TRONGRID_API_URL.rstrip('/')}/v1/accounts/{address}/transactions/trc20"
        f"?only_to=true&only_confirmed=true&limit={int(limit)}"
        f"&contract_address={USDT_TRC20_CONTRACT}"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
        },
    )
    api_key = os.environ.get("TRONGRID_API_KEY", "").strip()
    if api_key:
        req.add_header("TRON-PRO-API-KEY", api_key)
    fetch = opener or urllib.request.urlopen
    try:
        with fetch(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:180]
        except Exception:
            body = ""
        raise RuntimeError(f"TronGrid HTTP {exc.code}: {body or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach TronGrid: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("TronGrid returned invalid JSON") from exc
    return parse_trc20_transfers(payload)


def find_matching_payment(
    sku: str,
    machine_id: str,
    *,
    address: Optional[str] = None,
    txid: Optional[str] = None,
    now_ms: Optional[int] = None,
    transfers: Optional[List[Transfer]] = None,
    used_txids: Optional[List[str]] = None,
) -> Tuple[Optional[Transfer], Invoice]:
    addr = (address if address is not None else get_usdt_receive_address()).strip()
    invoice = build_invoice(sku, machine_id, address=addr)
    if transfers is None:
        transfers = fetch_incoming_usdt(addr)
    if now_ms is None:
        import time
        now_ms = int(time.time() * 1000)
    if used_txids is None:
        used_txids = load_used_txids()
    hit = match_payment(
        transfers,
        address=addr,
        amount_micros=invoice.amount_micros,
        now_ms=now_ms,
        used_txids=used_txids,
        txid=txid,
    )
    return hit, invoice


def fulfill_paid_plan(
    db,
    sku: str,
    machine_id: str,
    *,
    txid: Optional[str] = None,
    address: Optional[str] = None,
    now_ms: Optional[int] = None,
    transfers: Optional[List[Transfer]] = None,
    used_path: Optional[str] = None,
) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """If a matching USDT payment exists, issue and activate the license.

    Returns (ok, message, activation_key, txid).
    """
    addr = (address if address is not None else get_usdt_receive_address()).strip()
    if not addr:
        return False, "usdt_not_configured", None, None
    if not is_valid_tron_address(addr):
        return False, "usdt_bad_address", None, None
    if get_checkout_plan(sku) is None:
        return False, "unknown_plan", None, None

    used_file = used_path or _used_tx_path()
    try:
        hit, invoice = find_matching_payment(
            sku,
            machine_id,
            address=addr,
            txid=txid,
            now_ms=now_ms,
            transfers=transfers,
            used_txids=load_used_txids(used_file),
        )
    except Exception as exc:
        logger.error("USDT lookup failed: %s", exc)
        return False, f"lookup_failed:{exc}", None, None

    if hit is None:
        logger.info(
            "No matching USDT payment sku=%s amount=%s address=%s",
            sku, invoice.amount_usdt, addr,
        )
        return False, "payment_not_found", None, None

    from utils.license import issue_and_activate

    ok, message, key = issue_and_activate(db, sku, machine_id=machine_id)
    if ok:
        remember_txid(hit.txid, path=used_file)
        logger.info("USDT checkout fulfilled sku=%s tx=%s", sku, hit.txid)
        return True, message, key, hit.txid
    return False, message, None, hit.txid
