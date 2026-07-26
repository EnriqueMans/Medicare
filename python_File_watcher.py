"""
Simple file watcher - detects new files, logs them to Oracle, moves them.

Install: pip install watchdog python-oracledb
Run:     python simple_watcher.py
"""

import time
import shutil
import os
import socket
import oracledb
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "/data/inbound"
MOVE_TO   = "/data/processed"

ORACLE_USER = "myuser"
ORACLE_PWD  = "mypassword"
ORACLE_DSN  = "dbhost:1521/ORCLPDB1"   -- host:port/service_name


class Handler(FileSystemEventHandler):
    def __init__(self, conn):
        self.conn = conn

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        # give the file a moment to finish writing
        time.sleep(1)

        size = os.path.getsize(file_path)
        print(f"New file: {file_name} ({size} bytes)")

        dest = os.path.join(MOVE_TO, file_name)

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO file_watcher_log
                    (file_name, file_path, dest_path, file_size_bytes, host_name)
                VALUES
                    (:file_name, :file_path, :dest_path, :size, :host)
                """,
                {
                    "file_name": file_name,
                    "file_path": file_path,
                    "dest_path": dest,
                    "size": size,
                    "host": socket.gethostname(),
                },
            )
        self.conn.commit()
        print("Logged to Oracle.")

        shutil.move(file_path, dest)
        print(f"Moved to: {dest}")


if __name__ == "__main__":
    os.makedirs(MOVE_TO, exist_ok=True)

    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PWD, dsn=ORACLE_DSN)

    observer = Observer()
    observer.schedule(Handler(conn), WATCH_DIR, recursive=False)
    observer.start()
    print(f"Watching {WATCH_DIR}... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    conn.close()

