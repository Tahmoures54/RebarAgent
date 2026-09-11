from logic.inventory_apply import _parse_stock_row
from db.models import ScrapModel, ProjectModel


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
