"""Database helpers for the parser module."""

import logging
import sqlite3

from parser.models import Event

logger = logging.getLogger(__name__)


def insert_event(conn: sqlite3.Connection, event: Event) -> int:
    """Insert a normalised Event into the ``events`` table.

    Args:
        conn: Open SQLite connection (WAL mode expected).
        event: The normalised event to persist.

    Returns:
        The ``rowid`` (``id``) of the inserted row.

    Raises:
        sqlite3.Error: On any DB write failure (caller should catch).
    """
    cur = conn.execute(
        "INSERT INTO events (timestamp, source_ip, user, action, raw_log, source_type) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (event.timestamp, event.source_ip, event.user,
         event.action, event.raw_log, event.source_type),
    )
    conn.commit()
    logger.debug(
        "Inserted event id=%d type=%s action=%s", cur.lastrowid, event.source_type, event.action
    )
    return cur.lastrowid
