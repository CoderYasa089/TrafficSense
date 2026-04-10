from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import logging
from fpdf import FPDF

from database import get_connection, create_table, migrate_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TrafficSense Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
TICKET_DIR = os.path.join(BASE_DIR, "tickets")
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TICKET_DIR, exist_ok=True)


app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/tickets", StaticFiles(directory=TICKET_DIR), name="tickets")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


security = HTTPBearer()
ADMIN_TOKEN = "admin_secret_token"


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True


@app.on_event("startup")
def startup():
    create_table()
    migrate_database()


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
    pdf_path: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        return {"image_path": f"uploads/{file.filename}"}

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/violation")
def add_violation(v: Violation):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id FROM violations
            WHERE track_id=? AND violation_type=? AND video_time=?
            """,
            (v.track_id, v.violation_type, v.video_time),
        )

        if cur.fetchone():
            return {"message": "Duplicate ignored"}

        cur.execute(
            """
            INSERT INTO violations
            (time, camera_id, vehicle_type, vehicle_subtype, violation_type,
             speed, image_path, confidence, track_id, plate_number, video_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
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
                v.video_time,
            ),
        )

        conn.commit()
        vid = cur.lastrowid

        return {"message": "Violation stored", "violation_id": vid}

    finally:
        conn.close()


@app.post("/report_violation")
def report_violation(v: Violation):
    return add_violation(v)


@app.get("/violations")
def get_violations(auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT * FROM violations ORDER BY id DESC LIMIT 50"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@app.get("/violations/latest")
def latest_violation(auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT * FROM violations ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()

        if not row:
            return {"message": "No violations found"}

        return dict(row)

    finally:
        conn.close()


@app.get("/ticket/{violation_id}")
def generate_ticket(violation_id: int, auth: bool = Depends(verify_token)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT * FROM violations WHERE id=?",
            (violation_id,),
        )
        v = cur.fetchone()

        if not v:
            raise HTTPException(status_code=404, detail="Violation not found")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(0, 10, "Traffic Violation Ticket", ln=True)

        for k in v.keys():
            pdf.cell(0, 8, f"{k}: {v[k]}", ln=True)

        filename = f"ticket_{violation_id}.pdf"
        path = os.path.join(TICKET_DIR, filename)

        pdf.output(path)

        cur.execute(
            "UPDATE violations SET pdf_path=? WHERE id=?",
            (f"tickets/{filename}", violation_id),
        )
        conn.commit()

        return {"ticket_path": f"tickets/{filename}"}

    finally:
        conn.close()