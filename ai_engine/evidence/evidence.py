import cv2
from datetime import datetime
import os

BASE_DIR = "ai_engine/evidence/output"
os.makedirs(BASE_DIR, exist_ok=True)

def save_violation(frame, track_id):
    filename = f"{track_id}_{datetime.now().strftime('%H%M%S')}.jpg"
    path = os.path.join(BASE_DIR, filename)
    cv2.imwrite(path, frame)
    return path
