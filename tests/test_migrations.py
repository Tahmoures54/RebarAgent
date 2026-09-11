from db.database import DatabaseManager
from db.migrations import get_schema_version, SCHEMA_VERSION


def test_migrations_on_fresh_database(tmp_path):
    DatabaseManager.reset_instance()
    inst = DatabaseManager(db_path=str(tmp_path / "fresh.db"))
    assert inst.schema_version == SCHEMA_VERSION
    assert get_schema_version(inst.connection) == SCHEMA_VERSION
    DatabaseManager.reset_instance()


def test_failed_migration_does_not_advance(monkeypatch):
    import sqlite3
    import db.migrations as migrations

    conn = sqlite3.connect(":memory:")

    def boom(_conn):
        raise RuntimeError("forced failure")

    monkeypatch.setattr(migrations, "MIGRATIONS", [(1, boom)])
    monkeypatch.setattr(migrations, "SCHEMA_VERSION", 1)
    ver = migrations.run_migrations(conn)
    assert ver == 0
    assert migrations.get_schema_version(conn) == 0
