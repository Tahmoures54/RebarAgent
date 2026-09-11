from logic.validation import validate_position, validate_stock_coverage, summarize
from config import is_all_listofer_filter


def test_valid_straight_bar():
    issues = validate_position("00", {"L": 1000}, 12, 2, "bs")
    err, _warn, _info = summarize(issues)
    assert err == 0


def test_missing_shape_is_error():
    issues = validate_position("", {}, 12, 1)
    assert any(i.code == "shape.missing" for i in issues)


def test_invalid_diameter_and_qty():
    issues = validate_position("00", {"L": 1000}, 0, 0, "bs")
    codes = {i.code for i in issues}
    assert "diameter.invalid" in codes
    assert "quantity.invalid" in codes


def test_negative_dimension_is_error():
    issues = validate_position("00", {"L": -10}, 12, 1, "bs")
    assert any(i.code == "dimensions.negative" for i in issues)


def test_stock_coverage_warning():
    issues = validate_stock_coverage({16.0: 24000}, [])
    assert any(i.code == "stock.missing" for i in issues)


def test_all_listofer_filter_sentinels():
    assert is_all_listofer_filter(None)
    assert is_all_listofer_filter("")
    assert is_all_listofer_filter("-- Show All --")
    assert is_all_listofer_filter("-- نمایش همه --")
    assert not is_all_listofer_filter("F-01")
