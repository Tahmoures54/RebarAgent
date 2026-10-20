"""Regression tests for cutting-plan persistence failure reporting."""

from ui import cutting_plan_db


def test_save_plan_returns_false_when_sqlite_write_fails(monkeypatch):
    monkeypatch.setattr(cutting_plan_db, "_ensure_cutting_plans_table", lambda: None)

    def fail_connect(*args, **kwargs):
        raise OSError("simulated database unavailable")

    monkeypatch.setattr(cutting_plan_db.sqlite3, "connect", fail_connect)

    result = cutting_plan_db._save_plan(
        project_id=1,
        listofer_filter=None,
        stock_len=12.0,
        data_hash="test-hash",
        plans_per_group={(16.0, "A3"): {"plans": []}},
        status="confirmed",
    )

    assert result is False
