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
        violation_type TEXT,
        speed INTEGER,
        image_path TEXT
    )
    """)

    conn.commit()
    conn.close()

def insert_dummy():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO violations
    (time, camera_id, vehicle_type, violation_type, speed, image_path)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "2026-01-03 10:30",
        "CAM_01",
        "Car",
        "Over Speed",
        92,
        "images/car1.jpg"
    ))

    conn.commit()
    conn.close()
