from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from database import (
    create_table,
    insert_dummy,
    get_connection,
    migrate_database
)
from fpdf import FPDF
import os


app = FastAPI()

# ---------- Static Folders ----------
app.mount("/tickets", StaticFiles(directory="tickets"), name="tickets")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---------- Security Setup (STEP 12) ----------
security = HTTPBearer()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_TOKEN = "my_admin_secret_token"


# ---------- Startup ----------
@app.on_event("startup")
def startup():
    create_table()
    migrate_database()
    insert_dummy()


# ---------- Health Check ----------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Pydantic Models ----------
class Violation(BaseModel):
    time: str
    camera_id: str
    vehicle_type: str
    violation_type: str
    speed: int
    image_path: str
    confidence: float | None = None
    track_id: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ---------- Login API (STEP 12) ----------
@app.post("/login")
def login(data: LoginRequest):
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        return {
            "message": "Login successful",
            "token": ADMIN_TOKEN
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


# ---------- Token Verification ----------
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return True


# ---------- Admin Dashboard (PROTECTED) ----------
@app.get("/dashboard")
def dashboard(auth: bool = Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM violations")
    total = cursor.fetchone()[0]

    conn.close()

    return {
        "message": "Welcome Admin",
        "total_violations": total
    }


# ---------- PDF Ticket Generation ----------
def generate_ticket(violation_data: dict):
    if not os.path.exists("tickets"):
        os.makedirs("tickets")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Traffic Violation Ticket", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", size=12)

    for key, value in violation_data.items():
        pdf.cell(0, 8, f"{key}: {value}", ln=True)

    file_path = f"tickets/ticket_{violation_data['id']}.pdf"
    pdf.output(file_path)

    return file_path


# ---------- Upload Image ----------
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {
        "message": "Image uploaded successfully",
        "path": file_path
    }


# ---------- Add Violation ----------
@app.post("/violation")
def add_violation(v: Violation):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO violations
        (time, camera_id, vehicle_type, violation_type, speed, image_path, confidence, track_id)
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

    violation_id = cursor.lastrowid
    conn.commit()

    violation_data = {
        "id": violation_id,
        "time": v.time,
        "camera_id": v.camera_id,
        "vehicle_type": v.vehicle_type,
        "violation_type": v.violation_type,
        "speed": v.speed,
        "image_path": v.image_path,
        "confidence": v.confidence,
        "track_id": v.track_id
    }

    pdf_path = generate_ticket(violation_data)

    cursor.execute(
        "UPDATE violations SET pdf_path=? WHERE id=?",
        (pdf_path, violation_id)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Violation added successfully",
        "ticket_pdf": pdf_path
    }


# ---------- AI Integration API ----------
@app.post("/report_violation")
def report_violation(data: Violation):
    return add_violation(data)


# ---------- Get Violations ----------
@app.get("/violations")
def get_violations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM violations")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]



