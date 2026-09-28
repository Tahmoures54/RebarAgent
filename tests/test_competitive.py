from logic.competitive import first_fit_decreasing, format_duplicate_report, find_duplicate_marks


def test_ffd_packs_three_4m_on_two_12m():
    r = first_fit_decreasing([4, 4, 4, 4, 4], 12.0)
    assert r["bars"] == 2
    assert r["unfit"] == []
    assert r["waste_m"] == 4.0


def test_ffd_marks_oversize_unfit():
    r = first_fit_decreasing([13.0, 2.0], 12.0)
    assert r["unfit"] == [13.0]
    assert r["bars"] == 1


def test_duplicate_report_empty():
    assert "No duplicate" in format_duplicate_report([])
