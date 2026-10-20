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



def test_save_plan_returns_false_when_schema_setup_fails(monkeypatch):
    def fail_setup():
        raise OSError("simulated schema setup failure")

    monkeypatch.setattr(cutting_plan_db, "_ensure_cutting_plans_table", fail_setup)

    result = cutting_plan_db._save_plan(
        project_id=1,
        listofer_filter=None,
        stock_len=12.0,
        data_hash="test-hash",
        plans_per_group={(16.0, "A3"): {"plans": []}},
        status="draft",
    )

    assert result is False



def test_confirmed_plan_and_inventory_ledger_survive_reload(tmp_path, monkeypatch):
    db_path = str(tmp_path / "cutting_plan_cache.sqlite3")
    monkeypatch.setattr(cutting_plan_db, "DB_PATH", db_path)
    plans = {
        (16.0, "A3"): {"plans": [{"bar_length": 12.0, "bin": []}]},
        "_inventory_ledger": {
            "project_id": 7,
            "stock_bars_consumed": 1,
            "stock_consumed": [
                {"diameter": 16.0, "length_mm": 12000.0, "quantity": 1, "grade": "A3"}
            ],
        },
    }

    assert cutting_plan_db._save_plan(
        project_id=7,
        listofer_filter=None,
        stock_len=12.0,
        data_hash="stable-hash",
        plans_per_group=plans,
        status="confirmed",
    ) is True

    loaded, status = cutting_plan_db._load_plan(
        project_id=7,
        listofer_filter=None,
        stock_len=12.0,
        data_hash="stable-hash",
    )

    assert status == "confirmed"
    assert loaded[(16.0, "A3")]["plans"][0]["bar_length"] == 12.0
    assert loaded["_inventory_ledger"]["stock_bars_consumed"] == 1


def test_confirm_plan_reports_success_only_when_matching_row_exists(tmp_path, monkeypatch):
    db_path = str(tmp_path / "confirm_plan.sqlite3")
    monkeypatch.setattr(cutting_plan_db, "DB_PATH", db_path)

    assert cutting_plan_db._save_plan(
        project_id=9,
        listofer_filter=None,
        stock_len=12.0,
        data_hash="existing-hash",
        plans_per_group={(16.0, "A3"): {"plans": []}},
        status="draft",
    ) is True

    assert cutting_plan_db._confirm_plan(9, None, 12.0, "existing-hash") is True
    loaded, status = cutting_plan_db._load_plan(9, None, 12.0, "existing-hash")
    assert loaded is not None
    assert status == "confirmed"

    assert cutting_plan_db._confirm_plan(9, None, 12.0, "missing-hash") is False
