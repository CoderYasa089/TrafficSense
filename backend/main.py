from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
from fastapi import FastAPI
from pydantic import BaseModel
from database import create_table, insert_dummy, get_connection

app = FastAPI()

# ---------- Startup ----------
@app.on_event("startup")
def startup():
    create_table()
    insert_dummy()

# ---------- Health Check (YEH WAHI PEHLA CODE HAI) ----------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- Pydantic Model ----------
class Violation(BaseModel):
    time: str
    camera_id: str
    vehicle_type: str
    violation_type: str
    speed: int
    image_path: str

# ---------- POST /violation ----------
@app.post("/violation")
def add_violation(v: Violation):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO violations
    (time, camera_id, vehicle_type, violation_type, speed, image_path)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        v.time,
        v.camera_id,
        v.vehicle_type,
        v.violation_type,
        v.speed,
        v.image_path
    ))

    conn.commit()
    conn.close()

    return {"message": "Violation added successfully"}

# ---------- GET /violations ----------
@app.get("/violations")
def get_violations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM violations")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]



