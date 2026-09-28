import pytest
import logic.optimizer_stockflow as stockflow
from db.models import ProjectModel


def seed(db):
    project_id = ProjectModel.create("assignment-test", "test")
    listofer_id = db.execute("INSERT INTO listofers(project_id, number) VALUES (?, ?)", (project_id, "L-01"), commit=True)
    rebar_id = db.execute("INSERT INTO rebars(listofer_id, pos, diameter, quantity, grade) VALUES (?, ?, ?, ?, ?)", (listofer_id, "P1", 16.0, 1, "A3"), commit=True)
    stock_id = db.execute("INSERT INTO stock(project_id, diameter, length, quantity, grade) VALUES (?, ?, ?, ?, ?)", (project_id, 16.0, 12.0, 5, "A3"), commit=True)
    return project_id, rebar_id, stock_id


def plan():
    return [{"bar_length": 12.0, "stock_seq": 1, "scrap_id": None, "bin": [(5.0, {"item_idx": 0, "diameter": 16.0, "grade": "A3"})]}]


def test_assignment_uses_real_stock_id_and_is_idempotent(isolated_db, monkeypatch):
    project_id, rebar_id, stock_id = seed(isolated_db)
    monkeypatch.setattr(stockflow, "DB_PATH", isolated_db.db_path)
    stockflow.store_cutting_assignments(project_id, "L-01", plan(), {0: rebar_id})
    stockflow.store_cutting_assignments(project_id, "L-01", plan(), {0: rebar_id})
    rows = isolated_db.fetchall("SELECT rebar_id, source_type, source_id FROM cutting_assignments WHERE project_id=?", (project_id,))
    assert rows == [(rebar_id, "stock", stock_id)]


def test_assignment_refuses_source_reassignment(isolated_db, monkeypatch):
    project_id, rebar_id, stock_id = seed(isolated_db)
    monkeypatch.setattr(stockflow, "DB_PATH", isolated_db.db_path)
    stockflow.store_cutting_assignments(project_id, "L-01", plan(), {0: rebar_id})
    scrap_id = isolated_db.execute("INSERT INTO scraps(project_id, diameter, length_mm, grade) VALUES (?, ?, ?, ?)", (project_id, 16.0, 700.0, "A3"), commit=True)
    conflicting = [{"bar_length": 0.7, "scrap_id": scrap_id, "bin": [(0.5, {"item_idx": 0, "diameter": 16.0, "grade": "A3"})]}]
    with pytest.raises(ValueError, match="refusing reassignment"):
        stockflow.store_cutting_assignments(project_id, "L-01", conflicting, {0: rebar_id})
    assert isolated_db.fetchone("SELECT source_type, source_id FROM cutting_assignments WHERE rebar_id=?", (rebar_id,)) == ("stock", stock_id)
