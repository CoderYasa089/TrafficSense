from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from database import create_table, insert_dummy, get_connection
from fpdf import FPDF
import os


app = FastAPI()
app.mount("/tickets", StaticFiles(directory="tickets"), name="tickets")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---------- Startup ----------
@app.on_event("startup")
def startup():
    create_table()
    insert_dummy()

# ---------- Health Check ----------
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

# ---------- PDF Ticket Generation ----------
def generate_ticket(violation_data):
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

    violation_id = cursor.lastrowid
    conn.commit()

    violation_data = {
        "id": violation_id,
        "time": v.time,
        "camera_id": v.camera_id,
        "vehicle_type": v.vehicle_type,
        "violation_type": v.violation_type,
        "speed": v.speed,
        "image_path": v.image_path
    }

    pdf_path = generate_ticket(violation_data)

    # PDF path store in DB
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

# ---------- GET /violations ----------
@app.get("/violations")
def get_violations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM violations")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]
# ---------- Image Upload ----------
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):

    # uploads folder create if not exists
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {
        "message": "Image uploaded successfully",
        "path": file_path
    }




