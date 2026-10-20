"""Property-based checks for the independent cutting-plan validator."""

from hypothesis import given, strategies as st

from logic.optimizer_validation import validate_labeled_cutting_plans


positive_lengths = st.floats(
    min_value=0.05,
    max_value=5.0,
    allow_nan=False,
    allow_infinity=False,
)


@given(st.lists(positive_lengths, min_size=1, max_size=20), positive_lengths)
def test_validator_accepts_exact_demand_when_each_piece_has_its_own_bar(lengths, kerf):
    # Give each piece a bar with enough capacity for the validator's
    # conservative length + kerf convention.
    plans = [
        {"bar_length": length + kerf + 0.01, "bin": [(length, {})]}
        for length in lengths
    ]
    requested = [(length, {}) for length in lengths]

    assert validate_labeled_cutting_plans(plans, requested, kerf_m=kerf) == []


@given(positive_lengths)
def test_validator_rejects_piece_that_exceeds_bar_capacity(length):
    requested = [(length, {})]
    plans = [{"bar_length": length * 0.5, "bin": [(length, {})]}]

    errors = validate_labeled_cutting_plans(plans, requested)

    assert any("exceeds bar capacity" in error for error in errors)


@given(positive_lengths)
def test_validator_rejects_duplicate_piece(length):
    requested = [(length, {})]
    plans = [{"bar_length": length * 2.5, "bin": [(length, {}), (length, {})]}]

    errors = validate_labeled_cutting_plans(plans, requested)

    assert any("unrequested/duplicate" in error for error in errors)
