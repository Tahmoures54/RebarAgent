from utils.doctor import run_doctor


def test_doctor_core_checks_pass():
    report = run_doctor()
    names = [c.name for c in report.checks]
    assert "optimizer" in names
    assert "excel_import" in names
    assert "shape_registry" in names
    failed = [c for c in report.checks if not c.ok and c.level == "error"]
    assert not failed, report.as_text()
