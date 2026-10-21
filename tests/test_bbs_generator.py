import pytest

from config import WEIGHT_COEFFICIENT
from logic import bbs_generator


def _row(quantity=3):
    return (
        17, "LF-01", "Foundation", "P1", 10.0, "00", '{"A": 1000}',
        quantity, "Ground", "Beam", "tester", "2026-01-01", "A3", "bs",
    )


def test_generate_bbs_data_calculates_length_and_weight(monkeypatch):
    monkeypatch.setattr(
        bbs_generator.RebarModel,
        "get_for_project",
        staticmethod(lambda project_id, listofer_number=None: [_row()]),
    )
    monkeypatch.setattr(
        bbs_generator.default_shape_registry,
        "calc_shape_length",
        lambda shape, dimensions, diameter: 1000.0,
    )

    result = bbs_generator.generate_bbs_data(1)

    assert len(result) == 1
    item = result[0]
    assert item["id"] == 17
    assert item["dimensions"] == {"A": 1000}
    assert item["length_mm"] == pytest.approx(1000.0)
    assert item["unit_weight_kg"] == pytest.approx(100 * WEIGHT_COEFFICIENT)
    assert item["total_weight_kg"] == pytest.approx(300 * WEIGHT_COEFFICIENT)
    assert item["total_weight"] == item["total_weight_kg"]


def test_generate_bbs_data_keeps_row_when_shape_calculation_fails(monkeypatch):
    monkeypatch.setattr(
        bbs_generator.RebarModel,
        "get_for_project",
        staticmethod(lambda project_id, listofer_number=None: [_row(quantity=2)]),
    )

    def fail_calculation(*args, **kwargs):
        raise ValueError("unknown shape")

    monkeypatch.setattr(
        bbs_generator.default_shape_registry,
        "calc_shape_length",
        fail_calculation,
    )

    result = bbs_generator.generate_bbs_data(1)

    assert len(result) == 1
    assert result[0]["length_mm"] == 0.0
    assert result[0]["total_weight_kg"] == 0.0


def test_generate_bbs_data_passes_listofer_filter(monkeypatch):
    calls = []

    def fake_get(project_id, listofer_number=None):
        calls.append((project_id, listofer_number))
        return []

    monkeypatch.setattr(bbs_generator.RebarModel, "get_for_project", staticmethod(fake_get))

    assert bbs_generator.generate_bbs_data(8, "LF-22") == []
    assert calls == [(8, "LF-22")]
