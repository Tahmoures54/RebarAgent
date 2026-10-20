import pytest

import logic.optimizer_stockflow as stockflow
from logic.optimizer_options import OptimizerOptions


def _configure_stock_only(monkeypatch, plans):
    monkeypatch.setattr(stockflow, "get_scrap_infos_for_dia_grade", lambda *args: [])
    monkeypatch.setattr(stockflow, "get_available_stock_bars", lambda *args: {12.0: 5})
    monkeypatch.setattr(stockflow, "_pack_all_single_stock", lambda *args: (plans, []))


def test_stockflow_returns_plan_only_after_independent_validation(monkeypatch):
    items = [(5.0, {"pos": "A"}), (6.0, {"pos": "B"})]
    plans = [{"bar_length": 12.0, "bin": items.copy(), "scrap_id": None}]
    _configure_stock_only(monkeypatch, plans)

    result, new_scraps, usage = stockflow.optimize_with_scraps_and_stock(
        1, 16.0, "A3", items, 12.0,
        opts=OptimizerOptions(use_multi_stock=False),
    )

    assert result == plans
    assert new_scraps == []
    assert usage == {12.0: 1}


def test_stockflow_rejects_incomplete_plan_before_ui_or_inventory(monkeypatch):
    items = [(5.0, {"pos": "A"}), (6.0, {"pos": "B"})]
    plans = [{"bar_length": 12.0, "bin": [items[0]], "scrap_id": None}]
    _configure_stock_only(monkeypatch, plans)

    with pytest.raises(ValueError, match="failed independent physical validation.*missing requested"):
        stockflow.optimize_with_scraps_and_stock(
            1, 16.0, "A3", items, 12.0,
            opts=OptimizerOptions(use_multi_stock=False),
        )


def test_stockflow_rejects_plan_that_exceeds_capacity_after_kerf(monkeypatch):
    items = [(5.0, {"pos": "A"}), (4.9, {"pos": "B"})]
    plans = [{"bar_length": 10.0, "bin": items.copy(), "scrap_id": None}]
    _configure_stock_only(monkeypatch, plans)

    with pytest.raises(ValueError, match="exceeds bar capacity"):
        stockflow.optimize_with_scraps_and_stock(
            1, 16.0, "A3", items, 12.0,
            opts=OptimizerOptions(use_multi_stock=False, kerf_m=0.1),
        )
