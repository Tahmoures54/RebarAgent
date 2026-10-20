"""Tests for the startup database integrity gate."""
import sqlite3

from main import RebarAgentApp


class FakeDB:
    def __init__(self, connection):
        self.connection = connection


def test_startup_integrity_check_accepts_healthy_database(monkeypatch):
    app = RebarAgentApp.__new__(RebarAgentApp)
    app.db = FakeDB(sqlite3.connect(":memory:"))
    monkeypatch.setattr("main.messagebox.showerror", lambda *args, **kwargs: None)
    assert app._run_security_checks() is True
    app.db.connection.close()


def test_startup_integrity_check_rejects_database_connection_failure(monkeypatch):
    app = RebarAgentApp.__new__(RebarAgentApp)
    connection = sqlite3.connect(":memory:")
    connection.close()
    app.db = FakeDB(connection)
    monkeypatch.setattr("main.messagebox.showerror", lambda *args, **kwargs: None)
    assert app._run_security_checks() is False


def test_startup_integrity_check_rejects_failed_quick_check(monkeypatch):
    class BrokenConnection:
        def execute(self, sql):
            if sql == "PRAGMA quick_check":
                return self
            raise AssertionError("foreign_key_check should not run after quick_check failure")

        def fetchone(self):
            return ("database disk image is malformed",)

    app = RebarAgentApp.__new__(RebarAgentApp)
    app.db = FakeDB(BrokenConnection())
    monkeypatch.setattr("main.messagebox.showerror", lambda *args, **kwargs: None)
    assert app._run_security_checks() is False
