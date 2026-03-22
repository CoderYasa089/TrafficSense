import sqlite3
import os

# ✅ Always correct path (VERY IMPORTANT)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "traffic.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)

    # ✅ Row access like dict
    conn.row_factory = sqlite3.Row

    # ✅ Better concurrency (IMPORTANT for your system)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    return conn


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
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
    """)

    # ✅ Indexes (IMPORTANT for performance)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_track ON violations(track_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time ON violations(time)")

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
        "video_time": "REAL"
    }

    for column, col_type in columns.items():
        try:
            cursor.execute(f"ALTER TABLE violations ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            # Column already exists
            pass

    conn.commit()
    conn.close()