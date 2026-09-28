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


def test_apply_optimizer_shaped_plan_consumes_stock_and_scraps(isolated_db):
    """Real structure from optimize_with_scraps_and_stock must update inventory."""
    from db.models import ProjectModel, StockModel, ScrapModel
    from logic.inventory_apply import apply_cutting_plan_inventory, revert_cutting_plan_inventory

    pid = ProjectModel.create("opt-shape", "test")
    StockModel.add(pid, 16.0, 12000.0, 5, grade="A3")
    scrap_id = ScrapModel.add_scrap(pid, 16.0, 3500.0, grade="A3")

    plans_per_group = {
        (16.0, "A3"): {
            "plans": [
                {"bin": [(3.0, {"diameter": 16, "grade": "A3"})], "bar_length": 3.5, "scrap_id": scrap_id},
                {"bin": [(6.0, {"diameter": 16, "grade": "A3"}), (5.5, {"diameter": 16, "grade": "A3"})],
                 "bar_length": 12.0, "scrap_id": None, "stock_seq": 1},
                {"bin": [(4.0, {"diameter": 16, "grade": "A3"})],
                 "bar_length": 12.0, "scrap_id": None, "stock_seq": 2},
            ],
            "new_scraps": [0.5, 8.0],
            "stock_usage": {12.0: 2},
        }
    }

    ledger = apply_cutting_plan_inventory(pid, plans_per_group, 12.0)
    assert ledger["errors"] == []
    assert scrap_id in ledger["scraps_marked_used"]
    assert ledger["stock_bars_consumed"] == 2
    assert len(ledger["scraps_added_ids"]) == 2

    avail = ScrapModel.get_available_scraps(pid, 16.0, "A3")
    assert all(row[0] != scrap_id for row in avail)

    rows = StockModel.get_for_diameter(pid, 16.0, "A3")
    assert rows
    qty = rows[0][3]
    assert int(qty) == 3

    result = revert_cutting_plan_inventory(pid, ledger)
    assert result["ok"]
    assert result["restored_stock"] == 2
    rows = StockModel.get_for_diameter(pid, 16.0, "A3")
    assert int(rows[0][3]) == 5
    avail = ScrapModel.get_available_scraps(pid, 16.0, "A3")
    assert any(row[0] == scrap_id for row in avail)
    all_scraps = ScrapModel.get_all_scraps(pid, 16.0)
    assert len([s for s in all_scraps if s[5] in (0, False, "0")]) == 1


def test_hash_stable_across_confirm_used_flag(isolated_db, monkeypatch):
    """Unused-only hashing is deterministic after scraps are marked used."""
    from db.models import ProjectModel, ScrapModel
    from ui.cutting_plan_db import _compute_data_hash

    pid = ProjectModel.create("hash-stable", "test")
    ScrapModel.add_scrap(pid, 12.0, 1000.0, grade="A3")
    for s in ScrapModel.get_all_scraps(pid):
        ScrapModel.mark_as_used(s[0])
    h2 = _compute_data_hash(pid, None, 12.0)
    h3 = _compute_data_hash(pid, None, 12.0)
    assert h2 == h3
