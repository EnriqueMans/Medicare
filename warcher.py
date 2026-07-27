"""
file_watcher_db.py

Watches a directory for file events (created, modified, deleted, moved)
and records filenames + metadata into a SQLite database.

Install dependency first:
    pip install watchdog

Usage:
    python file_watcher_db.py /path/to/watch [--db files.db]
"""

import argparse
import os
import sqlite3
import time
from datetime import datetime, timezone

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS file_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


class DBHandler(FileSystemEventHandler):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _record(self, path: str, event_type: str):
        filename = os.path.basename(path)
        ts = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO file_events (filename, filepath, event_type, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (filename, path, event_type, ts),
        )
        self.conn.commit()
        print(f"[{ts}] {event_type.upper():8} {filename}")

    def on_created(self, event):
        if not event.is_directory:
            self._record(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self._record(event.src_path, "modified")

    def on_deleted(self, event):
        if not event.is_directory:
            self._record(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory:
            self._record(event.dest_path, "moved")


def main():
    parser = argparse.ArgumentParser(description="Watch a directory and log filenames to SQLite.")
    parser.add_argument("watch_dir", help="Directory to watch")
    parser.add_argument("--db", default="files.db", help="SQLite database path (default: files.db)")
    parser.add_argument("--recursive", action="store_true", help="Watch subdirectories too")
    args = parser.parse_args()

    conn = init_db(args.db)
    handler = DBHandler(conn)
    observer = Observer()
    observer.schedule(handler, args.watch_dir, recursive=args.recursive)
    observer.start()

    print(f"Watching '{args.watch_dir}' -> logging to '{args.db}'. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    conn.close()


if __name__ == "__main__":
    main()
