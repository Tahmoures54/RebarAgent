from utils.license import (
    activate_license,
    generate_activation_key,
    get_license_info,
    issue_and_activate,
)
from utils.usdt_payment import (
    Transfer,
    USDT_TRC20_CONTRACT,
    build_invoice,
    expected_amount_micros,
    fulfill_paid_plan,
    list_checkout_plans,
    match_payment,
    parse_trc20_transfers,
    unique_suffix_cents,
)


RECEIVE = "TXYZabcdefghjkmnpqrstuvwxyzzzzzzzz"


def _patch_license_store(monkeypatch, tmp_path):
    monkeypatch.setattr("utils.license.HIDDEN_DIR", str(tmp_path))
    monkeypatch.setattr("utils.license.HIDDEN_FILE", str(tmp_path / "license.dat"))
    monkeypatch.setattr("utils.usdt_payment.HIDDEN_LICENSE_DIR", str(tmp_path))


def test_checkout_plans_exclude_trial():
    skus = [p.sku for p in list_checkout_plans()]
    assert "trial" not in skus
    assert skus[0] == "pro_3m"
    assert "unlimited" in skus
    assert "office_1y" in skus


def test_unique_amount_is_stable_and_not_the_round_price():
    mid = "mac-aabbccddeeff"
    a = unique_suffix_cents(mid, "pro_1y")
    b = unique_suffix_cents(mid, "pro_1y")
    c = unique_suffix_cents("mac-other", "pro_1y")
    assert a == b
    assert 10 <= a <= 99
    assert a != c or unique_suffix_cents(mid, "pro_3m") != a
    micros = expected_amount_micros("pro_1y", mid)
    # $129 + 0.10–0.99
    assert 129_100_000 <= micros <= 129_990_000
    inv = build_invoice("pro_1y", mid, address=RECEIVE)
    assert inv.amount_usdt == f"{micros / 1_000_000:.2f}"
    assert inv.network == "TRC20"


def test_match_payment_requires_exact_usdt_amount_and_freshness():
    mid = "mac-aabbccddeeff"
    amount = expected_amount_micros("pro_3m", mid)
    now = 1_700_000_000_000
    good = Transfer(
        txid="tx-good",
        to_addr=RECEIVE,
        value_micros=amount,
        timestamp_ms=now - 60_000,
        contract=USDT_TRC20_CONTRACT,
        symbol="USDT",
    )
    wrong_amt = Transfer(
        txid="tx-amt",
        to_addr=RECEIVE,
        value_micros=amount - 10_000,
        timestamp_ms=now - 60_000,
        contract=USDT_TRC20_CONTRACT,
        symbol="USDT",
    )
    old = Transfer(
        txid="tx-old",
        to_addr=RECEIVE,
        value_micros=amount,
        timestamp_ms=now - (8 * 24 * 3600 * 1000),
        contract=USDT_TRC20_CONTRACT,
        symbol="USDT",
    )
    other_token = Transfer(
        txid="tx-usdc",
        to_addr=RECEIVE,
        value_micros=amount,
        timestamp_ms=now - 60_000,
        contract="TOtherTokenxxxxxxxxxxxxxxxxxxxxxxx",
        symbol="USDC",
    )
    assert match_payment(
        [wrong_amt, old, other_token, good],
        address=RECEIVE,
        amount_micros=amount,
        now_ms=now,
    ) == good
    assert match_payment(
        [good],
        address=RECEIVE,
        amount_micros=amount,
        now_ms=now,
        used_txids=["tx-good"],
    ) is None
    assert match_payment(
        [good],
        address=RECEIVE,
        amount_micros=amount,
        now_ms=now,
        txid="nope",
    ) is None


def test_parse_trongrid_payload():
    payload = {
        "data": [
            {
                "transaction_id": "abc",
                "to": RECEIVE,
                "value": "49000000",
                "block_timestamp": 123,
                "token_info": {
                    "symbol": "USDT",
                    "address": USDT_TRC20_CONTRACT,
                    "decimals": 6,
                },
            }
        ]
    }
    rows = parse_trc20_transfers(payload)
    assert len(rows) == 1
    assert rows[0].value_micros == 49_000_000
    assert rows[0].txid == "abc"


def test_generate_and_activate_key(isolated_db, tmp_path, monkeypatch):
    _patch_license_store(monkeypatch, tmp_path)
    monkeypatch.setattr("utils.license.get_machine_id", lambda: "mac-testmachine")
    key = generate_activation_key("mac-testmachine", "1year")
    ok, msg = activate_license(key, isolated_db)
    assert ok, msg
    info = get_license_info(isolated_db)
    assert info["type"] == "1year"
    assert info["remaining_days"] >= 360


def test_fulfill_paid_plan_issues_license(isolated_db, tmp_path, monkeypatch):
    _patch_license_store(monkeypatch, tmp_path)
    mid = "mac-paidcustomer"
    monkeypatch.setattr("utils.license.get_machine_id", lambda: mid)
    amount = expected_amount_micros("pro_6m", mid)
    now = 1_700_000_000_000
    transfers = [
        Transfer(
            txid="paid-tx-1",
            to_addr=RECEIVE,
            value_micros=amount,
            timestamp_ms=now - 30_000,
            contract=USDT_TRC20_CONTRACT,
            symbol="USDT",
        )
    ]
    ok, msg, key, txid = fulfill_paid_plan(
        isolated_db,
        "pro_6m",
        mid,
        address=RECEIVE,
        now_ms=now,
        transfers=transfers,
        used_path=str(tmp_path / "used_usdt_txids.json"),
    )
    assert ok, msg
    assert txid == "paid-tx-1"
    assert key
    info = get_license_info(isolated_db)
    assert info["type"] == "6month"

    # Same tx cannot be applied again on this machine store
    ok2, msg2, _, _ = fulfill_paid_plan(
        isolated_db,
        "pro_6m",
        mid,
        address=RECEIVE,
        now_ms=now,
        transfers=transfers,
        used_path=str(tmp_path / "used_usdt_txids.json"),
    )
    assert not ok2
    assert msg2 == "payment_not_found"


def test_fulfill_without_wallet(isolated_db, tmp_path, monkeypatch):
    _patch_license_store(monkeypatch, tmp_path)
    ok, msg, key, txid = fulfill_paid_plan(
        isolated_db, "pro_1y", "mac-x", address="", transfers=[],
    )
    assert not ok
    assert msg == "usdt_not_configured"
    assert key is None and txid is None


def test_issue_and_activate_unknown_plan(isolated_db):
    ok, msg, key = issue_and_activate(isolated_db, "nope", machine_id="mac-x")
    assert not ok
    assert key is None
    assert "Unknown" in msg
