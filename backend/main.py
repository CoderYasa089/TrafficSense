from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import os
import sqlite3
from fpdf import FPDF

from database import get_connection, create_table, migrate_database

app = FastAPI()

# -------------------------------
# STATIC FILES
# -------------------------------
os.makedirs("uploads", exist_ok=True)
os.makedirs("tickets", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/tickets", StaticFiles(directory="tickets"), name="tickets")

# -------------------------------
# SECURITY
# -------------------------------
security = HTTPBearer()
ADMIN_TOKEN = "admin_secret_token"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

# -------------------------------
# STARTUP
# -------------------------------
@app.on_event("startup")
def startup():
    create_table()
    migrate_database()

# -------------------------------
# MODELS
# -------------------------------
class Violation(BaseModel):
    time: str
    camera_id: str
    vehicle_type: str
    vehicle_subtype: Optional[str] = None
    violation_type: str
    speed: int
    image_path: str
    confidence: Optional[float] = None
    track_id: str
    plate_number: Optional[str] = None
    video_time: Optional[float] = None
    pdf_path: Optional[str] = None  # 🔥 FIX

# -------------------------------
# HEALTH
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------
# IMAGE UPLOAD
# -------------------------------
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"image_path": path}

# -------------------------------
# ADD VIOLATION
# -------------------------------
@app.post("/violation")
def add_violation(v: Violation):
    conn = get_connection()
    cur = conn.cursor()

    # 🔥 FIXED duplicate prevention
    cur.execute("""
    SELECT * FROM violations 
    WHERE track_id=? AND violation_type=?
    """, (v.track_id, v.violation_type))

    if cur.fetchone():
        conn.close()
        return {"message": "Duplicate ignored"}

    cur.execute("""
    INSERT INTO violations
    (time, camera_id, vehicle_type, vehicle_subtype, violation_type,
     speed, image_path, confidence, track_id, plate_number, video_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        v.time,
        v.camera_id,
        v.vehicle_type,
        v.vehicle_subtype,
        v.violation_type,
        v.speed,
        v.image_path,
        v.confidence,
        v.track_id,
        v.plate_number,
        v.video_time
    ))

    conn.commit()
    vid = cur.lastrowid
    conn.close()

    return {"message": "Violation stored", "violation_id": vid}

# -------------------------------
# AI ENTRY POINT
# -------------------------------
@app.post("/report_violation")
def report_violation(v: Violation):
    return add_violation(v)

# -------------------------------
# VIEW ALL VIOLATIONS
# -------------------------------
@app.get("/violations")
def get_violations(auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM violations")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# -------------------------------
# LATEST VIOLATION
# -------------------------------
@app.get("/violations/latest")
def latest_violation(auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM violations
    ORDER BY id DESC LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()

    if not row:
        return {"message": "No violations found"}

    return dict(row)

# -------------------------------
# FILTER VIOLATIONS
# -------------------------------
@app.get("/violations/filter")
def filter_violations(
    vehicle_type: str = None,
    violation_type: str = None,
    auth: bool = Depends(verify_token)
):
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM violations WHERE 1=1"
    params = []

    if vehicle_type:
        query += " AND vehicle_type=?"
        params.append(vehicle_type)

    if violation_type:
        query += " AND violation_type=?"
        params.append(violation_type)

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return rows

# -------------------------------
# ANALYTICS APIs
# -------------------------------
@app.get("/stats/total_violations")
def total_violations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM violations")
    total = cur.fetchone()[0]
    conn.close()
    return {"total_violations": total}

@app.get("/stats/by_vehicle")
def by_vehicle():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT vehicle_type, COUNT(*)
        FROM violations
        GROUP BY vehicle_type
    """)
    data = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return data

@app.get("/stats/by_camera")
def by_camera():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT camera_id, COUNT(*)
        FROM violations
        GROUP BY camera_id
    """)
    data = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return data

@app.get("/stats/peak_time")
def peak_time():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT substr(time, 12, 2) AS hour, COUNT(*)
        FROM violations
        GROUP BY hour
        ORDER BY COUNT(*) DESC
    """)
    data = {f"{row[0]}:00": row[1] for row in cur.fetchall()}
    conn.close()
    return data

# -------------------------------
# PDF GENERATION
# -------------------------------
@app.get("/ticket/{violation_id}")
def generate_ticket(violation_id: int, auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM violations WHERE id=?", (violation_id,))
    v = cur.fetchone()

    if not v:
        conn.close()
        raise HTTPException(status_code=404, detail="Violation not found")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Traffic Violation Ticket", ln=True)

    for k in v.keys():
        pdf.cell(0, 8, f"{k}: {v[k]}", ln=True)

    path = f"tickets/ticket_{violation_id}.pdf"
    pdf.output(path)

    cur.execute("UPDATE violations SET pdf_path=? WHERE id=?", (path, violation_id))
    conn.commit()
    conn.close()

    return {"ticket_path": path}