import sqlite3

DB_NAME = "traffic.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
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

    # Optional performance index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_track ON violations(track_id)")
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
            pass

    conn.commit()
    conn.close()