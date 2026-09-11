import pandas as pd

from utils.excel_import import (
    _map_columns,
    _shape_dimensions,
    create_import_template,
    import_rebars_from_excel,
    normalize_shape_code,
    normalize_standard,
    read_import_preview,
)


def test_persian_column_map():
    mapped = _map_columns(["لیستوفر", "پوز", "قطر", "شکل", "تعداد", "طول"])
    assert mapped["diameter"] == "قطر"
    assert mapped["quantity"] == "تعداد"
    assert mapped["shape"] == "شکل"
    assert mapped["a"] == "طول"


def test_shape_and_standard_helpers():
    assert normalize_shape_code("21 - U-stirrup") == "21"
    assert normalize_standard("Mabhas 9") == "ir"
    assert normalize_standard("مبحث9") == "ir"
    assert _shape_dimensions("00", {"A": 1800})["L"] == 1800


def test_template_and_dry_run(tmp_path):
    path = str(tmp_path / "tpl.xlsx")
    create_import_template(path)
    preview = read_import_preview(path)
    assert preview["rows"] == 2
    assert not preview["missing_required"]
    result = import_rebars_from_excel(path, project_id=1, dry_run=True)
    assert result["imported"] == 2
    assert result["dry_run"] is True
    assert result["errors"] == []


def test_persian_workbook_dry_run(tmp_path):
    path = str(tmp_path / "fa.xlsx")
    pd.DataFrame(
        [{"قطر": 16, "تعداد": 4, "شکل": "00", "طول": 2500, "پوز": "B1"}]
    ).to_excel(path, index=False)
    result = import_rebars_from_excel(path, project_id=1, dry_run=True)
    assert result["imported"] == 1
    assert result["errors"] == []
