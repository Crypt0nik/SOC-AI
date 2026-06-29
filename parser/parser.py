"""SOC-AI parser module — real-time log ingestion via Watchdog.

Watches ``LOG_DIR`` for new/modified log files, parses each line into a
normalised :class:`~parser.models.Event`, and writes it to the ``events``
table in SQLite.  Windows Event XML files are buffered until a complete
``<Event>...</Event>`` block is available.
"""

import logging
import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from db.init_db import init_db
from parser.db import insert_event
from parser.formats import detect_source_type, parse_line
from parser.formats.windows import parse_windows_xml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("soc_ai.parser")

_XML_CLOSE_TAG = "</Event>"


class LogFileHandler(FileSystemEventHandler):
    """Watchdog event handler that tails log files and pushes Events to SQLite."""

    def __init__(self, conn) -> None:
        """Initialise the handler with a database connection.

        Args:
            conn: Open SQLite connection (WAL mode).
        """
        super().__init__()
        self._conn = conn
        # Per-file byte offset (to avoid re-processing already-seen lines)
        self._offsets: dict[str, int] = {}
        # Per-file XML accumulation buffer for Windows Event logs
        self._xml_buffers: dict[str, str] = {}

    def on_created(self, event) -> None:
        """Handle a new file appearing in the watched directory.

        Args:
            event: Watchdog FileCreatedEvent.
        """
        if not event.is_directory:
            self._offsets[event.src_path] = 0
            logger.info("New file: %s", event.src_path)
            self._process_file(event.src_path)

    def on_modified(self, event) -> None:
        """Handle a file modification (new content appended).

        Args:
            event: Watchdog FileModifiedEvent.
        """
        if not event.is_directory:
            self._process_file(event.src_path)

    def _process_file(self, filepath: str) -> None:
        """Read new content from ``filepath`` since last offset and dispatch.

        Args:
            filepath: Absolute path to the log file.
        """
        source_type = detect_source_type(filepath)
        offset = self._offsets.get(filepath, 0)

        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                # Detect truncation (log rotation)
                f.seek(0, 2)
                file_size = f.tell()
                if file_size < offset:
                    logger.info("File truncated (rotation?): %s — resetting offset", filepath)
                    offset = 0
                    self._xml_buffers.pop(filepath, None)
                f.seek(offset)
                new_content = f.read()
                self._offsets[filepath] = f.tell()
        except OSError as exc:
            logger.warning("Cannot read %s: %s", filepath, exc)
            return

        if not new_content:
            return

        if source_type == "windows":
            self._process_xml(filepath, new_content)
        else:
            for line in new_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = parse_line(line, source_type)
                    if evt:
                        insert_event(self._conn, evt)
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to process line from %s: %s | line=%.80r", filepath, exc, line
                    )

    def _process_xml(self, filepath: str, content: str) -> None:
        """Accumulate content until complete ``<Event>`` blocks can be parsed.

        Args:
            filepath: Path used as buffer key.
            content: New XML content chunk to append to the buffer.
        """
        buf = self._xml_buffers.get(filepath, "") + content
        while _XML_CLOSE_TAG in buf:
            end = buf.index(_XML_CLOSE_TAG) + len(_XML_CLOSE_TAG)
            block = buf[:end]
            buf = buf[end:]
            start = block.find("<Event")
            if start == -1:
                continue
            xml_block = block[start:]
            try:
                evt = parse_windows_xml(xml_block)
                if evt:
                    insert_event(self._conn, evt)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to parse Windows XML block from %s: %s", filepath, exc)
        self._xml_buffers[filepath] = buf


def main() -> None:
    """Entry point — watch ``LOG_DIR`` and push events to SQLite."""
    log_dir = os.environ.get("LOG_DIR", "/logs")
    db_path = os.environ.get("DB_PATH", "/data/soc.db")

    conn = init_db(db_path)
    logger.info("Parser started. Watching directory: %s", log_dir)

    handler = LogFileHandler(conn)
    observer = Observer()
    observer.schedule(handler, log_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Parser shutting down...")
    finally:
        observer.stop()
        observer.join()
        conn.close()
        logger.info("Parser stopped.")


if __name__ == "__main__":
    main()
