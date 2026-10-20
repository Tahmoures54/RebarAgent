import pytest

from logic.optimizer_validation import validate_labeled_cutting_plans


def test_valid_plan_covers_exact_demand_and_capacity():
    plans = [
        {"bar_length": 12.0, "bin": [(5.0, {"pos": "A"}), (5.0, {"pos": "B"})]},
        {"bar_length": 8.0, "bin": [(7.0, {"pos": "C"})], "scrap_id": 3},
    ]
    requested = [(5.0, {}), (5.0, {}), (7.0, {})]
    assert validate_labeled_cutting_plans(plans, requested) == []


def test_rejects_missing_or_duplicate_demand():
    plans = [{"bar_length": 12.0, "bin": [(5.0, {}), (5.0, {})]}]
    requested = [(5.0, {}), (4.0, {})]
    errors = validate_labeled_cutting_plans(plans, requested)
    assert any("missing requested" in error for error in errors)
    assert any("unrequested/duplicate" in error for error in errors)


def test_rejects_capacity_overrun_after_kerf():
    plans = [{"bar_length": 10.0, "bin": [(5.0, {}), (4.9, {})]}]
    errors = validate_labeled_cutting_plans(
        plans, [(5.0, {}), (4.9, {})], kerf_m=0.1
    )
    assert any("exceeds bar capacity" in error for error in errors)


@pytest.mark.parametrize("length", [0, -1, float("nan"), float("inf")])
def test_rejects_non_physical_piece_lengths(length):
    plans = [{"bar_length": 12.0, "bin": [(length, {})]}]
    errors = validate_labeled_cutting_plans(plans, [(length, {})])
    assert errors


def test_rejects_invalid_kerf():
    assert validate_labeled_cutting_plans([], [], kerf_m=-0.01)
