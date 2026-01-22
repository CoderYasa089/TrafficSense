from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import os
import sqlite3
from fpdf import FPDF

from database import get_connection, migrate_database

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
ADMIN_TOKEN = "my_admin_secret_token"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

# -------------------------------
# STARTUP
# -------------------------------
@app.on_event("startup")
def startup():
    migrate_database()

# -------------------------------
# MODELS
# -------------------------------
class Violation(BaseModel):
    time: str
    camera_id: str
    vehicle_type: str
    violation_type: str
    speed: int
    image_path: str
    confidence: Optional[float] = None
    track_id: str

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
# ADD VIOLATION (NO PDF HERE)
# -------------------------------
@app.post("/violation")
def add_violation(v: Violation):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
        INSERT INTO violations
        (time, camera_id, vehicle_type, violation_type,
         speed, image_path, confidence, track_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v.time,
            v.camera_id,
            v.vehicle_type,
            v.violation_type,
            v.speed,
            v.image_path,
            v.confidence,
            v.track_id
        ))

        conn.commit()
        vid = cur.lastrowid

    except sqlite3.IntegrityError:
        conn.close()
        return {"message": "Duplicate violation ignored"}

    conn.close()
    return {"message": "Violation stored", "violation_id": vid}

# -------------------------------
# AI ENTRY POINT
# -------------------------------
@app.post("/report_violation")
def report_violation(v: Violation):
    return add_violation(v)

# -------------------------------
# JAN-22 ANALYTICS APIs ✅
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
# JAN-23 PDF (ON DEMAND ONLY) ✅
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

# -------------------------------
# VIEW VIOLATIONS
# -------------------------------
@app.get("/violations")
def get_violations(auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM violations")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows






