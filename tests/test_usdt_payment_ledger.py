import json

import pytest

from utils import usdt_payment


def test_missing_used_txid_ledger_is_empty(tmp_path):
    assert usdt_payment.load_used_txids(str(tmp_path / "missing.json")) == []


def test_used_txid_ledger_is_deduplicated_and_written_atomically(tmp_path):
    path = tmp_path / "used.json"
    usdt_payment.remember_txid("tx-a", str(path))
    usdt_payment.remember_txid("tx-a", str(path))
    usdt_payment.remember_txid("tx-b", str(path))

    assert usdt_payment.load_used_txids(str(path)) == ["tx-a", "tx-b"]
    assert json.loads(path.read_text(encoding="utf-8")) == {"txids": ["tx-a", "tx-b"]}
    assert not list(tmp_path.glob(".used_txids_*.tmp"))


@pytest.mark.parametrize(
    "raw",
    [
        "{broken",
        "null",
        '{"txids": "not-a-list"}',
        '{"txids": ["tx-a", ""]}',
    ],
)
def test_corrupt_used_txid_ledger_fails_closed(tmp_path, raw):
    path = tmp_path / "used.json"
    path.write_text(raw, encoding="utf-8")

    with pytest.raises(RuntimeError, match="ledger|transaction ID"):
        usdt_payment.load_used_txids(str(path))


def test_remember_txid_rejects_empty_identifier(tmp_path):
    with pytest.raises(ValueError, match="must not be empty"):
        usdt_payment.remember_txid(" ", str(tmp_path / "used.json"))
