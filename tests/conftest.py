"""Shared pytest fixtures for SOC-AI tests."""

import sqlite3
import sys
from pathlib import Path

import pytest

# Ensure repo root is importable regardless of how pytest is invoked
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    """Create a fresh temporary SQLite database for each test.

    Sets the DB_PATH environment variable so that modules using
    ``db.init_db.get_connection()`` pick up the temp path.

    Returns:
        Path: path to the temporary database file.
    """
    db_file = tmp_path / "test_soc.db"
    monkeypatch.setenv("DB_PATH", str(db_file))

    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    schema_sql = schema_path.read_text()
    for stmt in schema_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass
    conn.commit()
    return db_file, conn
