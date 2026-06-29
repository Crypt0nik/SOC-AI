"""Shared SQLite initialisation helper used by all SOC-AI modules."""

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a WAL-mode SQLite connection with foreign-key enforcement.

    Args:
        db_path: Path to the SQLite file.  Defaults to the DB_PATH env var,
                 then to ``/data/soc.db``.

    Returns:
        sqlite3.Connection with row_factory set to ``sqlite3.Row``.
    """
    path = db_path or os.environ.get("DB_PATH", "/data/soc.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    """Initialise the database schema (idempotent, safe to call on every startup).

    Args:
        db_path: Path to the SQLite file.

    Returns:
        An open sqlite3.Connection.
    """
    conn = get_connection(db_path)
    schema_sql = _SCHEMA_PATH.read_text()
    # Execute statement by statement to avoid issues with multi-statement execute
    for stmt in schema_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as exc:
                # PRAGMA statements may raise "cannot execute in a transaction" → safe to ignore
                logger.debug("Schema stmt skipped (%s): %s", exc, stmt[:60])
    conn.commit()
    logger.info("Database initialised at %s", db_path or os.environ.get("DB_PATH", "/data/soc.db"))
    return conn
