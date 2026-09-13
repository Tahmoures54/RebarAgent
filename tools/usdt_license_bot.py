# tools/usdt_license_bot.py
"""Optional Telegram sales bot: customer sends Machine ID + plan, pays USDT TRC20,
the bot checks TronGrid and replies with an activation key.

This is NOT a Cursor cloud worker. Run it on a machine you control:

    export REBARAGENT_TELEGRAM_BOT_TOKEN=123:abc
    export REBARAGENT_USDT_TRC20=TYourTronAddress...
    python tools/usdt_license_bot.py

Customers: /start → pick plan → send Machine ID → pay exact amount → /check
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.envfile import load_env_file
load_env_file(os.path.join(ROOT, ".env"))

from utils.license import generate_activation_key, PLAN_SKU_TO_LICENSE_TYPE
from utils.usdt_payment import (
    build_invoice,
    find_matching_payment,
    get_checkout_plan,
    get_usdt_receive_address,
    is_valid_tron_address,
    list_checkout_plans,
    remember_txid,
)


STATE_PATH = os.path.join(os.environ.get("REBARAGENT_BOT_STATE", ROOT), "telegram_bot_state.json")
API = "https://api.telegram.org/bot{token}/{method}"


def _token() -> str:
    token = os.environ.get("REBARAGENT_TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set REBARAGENT_TELEGRAM_BOT_TOKEN")
    return token


def _load_state() -> dict:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"offset": 0, "chats": {}}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH) or ".", exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_PATH)


def _api(token: str, method: str, payload: dict | None = None, timeout: int = 35) -> dict:
    url = API.format(token=token, method=method)
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _send(token: str, chat_id: int, text: str) -> None:
    _api(token, "sendMessage", {"chat_id": chat_id, "text": text})


def _help_text() -> str:
    lines = [
        "RebarAgent — خرید خودکار با تتر (TRC20)",
        "",
        "۱) یکی از پلن‌ها را بفرستید:",
    ]
    for plan in list_checkout_plans():
        days = "مادام‌العمر" if plan.days is None else f"{plan.days} روز"
        lines.append(f"   /{plan.sku}  {plan.name_fa} — {days} — {plan.price_usd} USDT")
    lines += [
        "",
        "۲) شناسه سیستم (Machine ID) را از پنجره لایسنس برنامه کپی کنید و اینجا بفرستید.",
        "۳) دقیقاً مبلغ اعلام‌شده را روی شبکه TRC20 بفرستید.",
        "۴) /check را بزنید تا کلید فعال‌سازی برایتان ارسال شود.",
        "",
        "شبکه اشتباه (ERC20/BEP20) قابل برگشت نیست.",
    ]
    return "\n".join(lines)


def _handle_text(token: str, state: dict, chat_id: int, text: str) -> None:
    text = (text or "").strip()
    chats = state.setdefault("chats", {})
    chat = chats.setdefault(str(chat_id), {})
    low = text.lower()

    if low in {"/start", "/help", "start", "help", "راهنما"}:
        _send(token, chat_id, _help_text())
        return

    sku = low[1:] if low.startswith("/") else low
    plan = get_checkout_plan(sku)
    if plan is not None:
        chat["sku"] = plan.sku
        _save_state(state)
        if chat.get("machine_id"):
            _send_invoice(token, chat_id, chat)
        else:
            _send(
                token,
                chat_id,
                f"پلن «{plan.name_fa}» انتخاب شد.\nشناسه سیستم را از برنامه کپی کنید و اینجا بفرستید.",
            )
        return

    if low in {"/check", "check", "پرداخت کردم", "پرداخت شدم"}:
        _check_payment(token, chat_id, chat)
        return

    if text.lower().startswith("mac-") or (len(text) >= 8 and " " not in text and "|" not in text):
        chat["machine_id"] = text
        _save_state(state)
        if chat.get("sku"):
            _send_invoice(token, chat_id, chat)
        else:
            _send(token, chat_id, "شناسه ذخیره شد. حالا پلن را با دستور /pro_1y (یا پلن دیگر) انتخاب کنید.")
        return

    _send(token, chat_id, _help_text())


def _send_invoice(token: str, chat_id: int, chat: dict) -> None:
    addr = get_usdt_receive_address()
    if not is_valid_tron_address(addr):
        _send(token, chat_id, "کیف‌پول تتر روی سرور تنظیم نشده. بعداً دوباره تلاش کنید.")
        return
    invoice = build_invoice(chat["sku"], chat["machine_id"], address=addr)
    plan = get_checkout_plan(chat["sku"])
    _send(
        token,
        chat_id,
        "\n".join(
            [
                f"پلن: {plan.name_fa if plan else invoice.sku}",
                f"شبکه: {invoice.network} (فقط ترون)",
                f"آدرس:\n{invoice.address}",
                f"مبلغ دقیق:\n{invoice.amount_usdt} USDT",
                "",
                "همین مبلغ را بفرستید (نه عدد گرد). بعد از تأیید شبکه /check را بزنید.",
            ]
        ),
    )


def _check_payment(token: str, chat_id: int, chat: dict) -> None:
    sku = chat.get("sku")
    machine_id = chat.get("machine_id")
    if not sku or not machine_id:
        _send(token, chat_id, "اول پلن و شناسه سیستم را بفرستید. /start")
        return
    addr = get_usdt_receive_address()
    try:
        hit, invoice = find_matching_payment(sku, machine_id, address=addr)
    except Exception as exc:
        _send(token, chat_id, f"بررسی زنجیره ممکن نشد: {exc}")
        return
    if hit is None:
        _send(
            token,
            chat_id,
            f"پرداخت {invoice.amount_usdt} USDT هنوز دیده نشد. یک دقیقه صبر کنید و /check را دوباره بزنید.",
        )
        return
    lic_type = PLAN_SKU_TO_LICENSE_TYPE[sku]
    key = generate_activation_key(machine_id, lic_type)
    remember_txid(hit.txid)
    _send(
        token,
        chat_id,
        "\n".join(
            [
                "پرداخت تأیید شد. کلید فعال‌سازی:",
                key,
                "",
                "در برنامه: مدیریت لایسنس → چسباندن کلید → فعال‌سازی.",
                f"txid: {hit.txid}",
            ]
        ),
    )


def main() -> None:
    addr = get_usdt_receive_address()
    if not is_valid_tron_address(addr):
        raise SystemExit("Set REBARAGENT_USDT_TRC20 to a valid TRC20 address first.")
    token = _token()
    state = _load_state()
    print(f"USDT license bot polling. Receive {addr}", flush=True)
    while True:
        try:
            payload = _api(
                token,
                "getUpdates",
                {"timeout": 25, "offset": int(state.get("offset") or 0)},
                timeout=40,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print("poll error:", exc, flush=True)
            time.sleep(3)
            continue
        if not payload.get("ok"):
            time.sleep(2)
            continue
        for upd in payload.get("result") or []:
            state["offset"] = int(upd["update_id"]) + 1
            msg = upd.get("message") or upd.get("edited_message") or {}
            text = msg.get("text")
            chat = (msg.get("chat") or {}).get("id")
            if text and chat is not None:
                try:
                    _handle_text(token, state, int(chat), text)
                except Exception as exc:
                    print("handle error:", exc, flush=True)
            _save_state(state)


if __name__ == "__main__":
    main()
