import pytest

from logic.inventory_apply import _parse_stock_row
from db.models import ScrapModel, ProjectModel
import logic.inventory_apply as inventory_apply


def test_parse_stock_row_five_and_six_columns():
    five = _parse_stock_row((7, 16.0, 12000.0, 5, "A3"))
    assert five == (7, 12000.0, 5)
    six = _parse_stock_row((7, 99, 16.0, 12000.0, 5, "A3"))
    assert six == (7, 12000.0, 5)


def test_identical_scraps_are_not_merged(isolated_db):
    pid = ProjectModel.create("scrap-uniq", "test")
    a = ScrapModel.add_scrap(pid, 16.0, 800.0, grade="A3")
    b = ScrapModel.add_scrap(pid, 16.0, 800.0, grade="A3")
    assert a != b
    rows = ScrapModel.get_available_scraps(pid, 16.0, "A3")
    assert len(rows) == 2


def test_apply_aborts_when_stock_consumption_fails(monkeypatch):
    monkeypatch.setattr(inventory_apply, "_consume_stock_bar", lambda *args: False)

    with pytest.raises(RuntimeError, match="Inventory apply aborted"):
        inventory_apply.apply_cutting_plan_inventory(
            1,
            {"plans": [{"bars": [{"diameter": 16, "length_m": 12, "quantity": 2}]}]},
            12,
        )


def test_apply_records_successful_stock_consumption(monkeypatch):
    monkeypatch.setattr(inventory_apply, "_consume_stock_bar", lambda *args: True)

    ledger = inventory_apply.apply_cutting_plan_inventory(
        1,
        {"plans": [{"bars": [{"diameter": 16, "length_m": 12, "quantity": 2}]}]},
        12,
    )

    assert ledger["stock_bars_consumed"] == 2
    assert ledger["stock_consumed"] == [
        {"diameter": 16.0, "length_mm": 12000.0, "quantity": 2, "grade": None}
    ]
    assert ledger["errors"] == []


def test_apply_rolls_back_successful_mutations_when_later_mutation_fails(monkeypatch):
    marked = []
    unmarked = []
    monkeypatch.setattr(inventory_apply, "_mark_scrap_used_raw", lambda sid: marked.append(sid) or True)
    monkeypatch.setattr(inventory_apply, "_mark_scrap_unused_raw", lambda sid: unmarked.append(sid) or True)
    monkeypatch.setattr(inventory_apply, "_consume_stock_bar", lambda *args: False)

    with pytest.raises(RuntimeError):
        inventory_apply.apply_cutting_plan_inventory(
            1,
            {"plans": [{"bars": [{"scrap_ids": [42], "diameter": 16, "length_m": 12, "quantity": 1}]}]},
            12,
        )

    assert marked == [42]
    assert unmarked == [42]


def test_empty_ledger_is_not_successful_rollback():
    result = inventory_apply.revert_cutting_plan_inventory(1, {})
    assert result["ok"] is False
    assert result["errors"] == ["empty ledger"]
