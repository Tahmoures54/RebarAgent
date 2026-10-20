"""Security regression tests for USDT transfer matching.

These tests exercise deterministic matching only; they do not claim to verify
live-chain finality or make client-side license issuance trustworthy.
"""
from utils import usdt_payment as payment


def _transfer(**overrides):
    values = {
        "txid": "tx-unique-1",
        "to_addr": "TRecipient",
        "value_micros": 12_345_000,
        "timestamp_ms": 1_000_000,
        "contract": payment.USDT_TRC20_CONTRACT,
        "symbol": "USDT",
    }
    values.update(overrides)
    return payment.Transfer(**values)


def _match(tx, **overrides):
    options = {
        "address": "TRecipient",
        "amount_micros": 12_345_000,
        "now_ms": 1_000_000 + 60_000,
        "max_age_sec": 600,
    }
    options.update(overrides)
    return payment.match_payment([tx], **options)


def test_match_payment_accepts_exact_confirmed_transfer_metadata():
    tx = _transfer()
    assert _match(tx) == tx


def test_match_payment_rejects_wrong_recipient_amount_contract_or_symbol():
    assert _match(_transfer(to_addr="TOther")) is None
    assert _match(_transfer(value_micros=12_344_000)) is None
    assert _match(_transfer(contract="TWrongContract")) is None
    assert _match(_transfer(symbol="OTHER")) is None
    assert _match(_transfer(contract="")) is None
    assert _match(_transfer(symbol="")) is None


def test_match_payment_rejects_missing_or_invalid_timestamp():
    assert _match(_transfer(timestamp_ms=0)) is None
    assert _match(_transfer(timestamp_ms=1_100_000)) is None
    assert _match(_transfer(timestamp_ms=1)) is None


def test_match_payment_rejects_used_txid_and_honors_explicit_txid():
    tx = _transfer()
    assert _match(tx, used_txids=[tx.txid]) is None
    assert _match(tx, txid="another-tx") is None
    assert _match(tx, txid=tx.txid) == tx


def test_match_payment_rejects_empty_transaction_id():
    assert _match(_transfer(txid="")) is None
