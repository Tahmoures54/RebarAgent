from logic.sample_project import create_sample_project, SAMPLE_NAME
from db.models import RebarModel, ProjectModel
from shapes.definitions import default_shape_registry
import json


def test_sample_project_straight_bars_use_L(isolated_db):
    info = create_sample_project(force=True)
    assert info["rebars"] >= 8
    assert info["name"] == SAMPLE_NAME
    rows = RebarModel.get_for_project(info["project_id"])
    assert rows
    zero = 0
    for row in rows:
        shape = row[5]
        dims = row[6]
        if isinstance(dims, str):
            dims = json.loads(dims or "{}")
        dia = row[4]
        length = default_shape_registry.calc_shape_length(shape, dims, float(dia))
        if length <= 0:
            zero += 1
    assert zero == 0
    # Existing sample is reused when not forced
    again = create_sample_project(force=False)
    assert again["existing"] is True
    assert again["project_id"] == info["project_id"]
    assert len(ProjectModel.get_all()) == 1
