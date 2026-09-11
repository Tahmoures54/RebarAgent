import pytest

from config import is_all_listofer_filter


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Bind models to a throwaway SQLite file."""
    import db.database as database
    import db.models as models

    database.DatabaseManager.reset_instance()
    path = str(tmp_path / "rebar_test.db")
    inst = database.DatabaseManager(db_path=path)
    monkeypatch.setattr(database, "db", inst)
    monkeypatch.setattr(models, "db", inst)
    yield inst
    database.DatabaseManager.reset_instance()
