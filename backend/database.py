import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "traffic.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            camera_id TEXT,
            vehicle_type TEXT,
            vehicle_subtype TEXT,
            violation_type TEXT,
            speed INTEGER,
            image_path TEXT,
            pdf_path TEXT,
            confidence REAL,
            track_id TEXT,
            plate_number TEXT,
            video_time REAL
        )
        """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_track ON violations(track_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_time ON violations(time)"
    )

    conn.commit()
    conn.close()


def migrate_database():
    conn = get_connection()
    cursor = conn.cursor()

    columns = {
        "pdf_path": "TEXT",
        "confidence": "REAL",
        "track_id": "TEXT",
        "vehicle_subtype": "TEXT",
        "plate_number": "TEXT",
        "video_time": "REAL",
    }

    for column, col_type in columns.items():
        try:
            cursor.execute(
                f"ALTER TABLE violations ADD COLUMN {column} {col_type}"
            )
        except sqlite3.OperationalError:
            continue

    conn.commit()
    conn.close()