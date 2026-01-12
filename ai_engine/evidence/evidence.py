import cv2
from datetime import datetime
import os

os.makedirs("ai_engine/evidence/output", exist_ok=True)

def save_violation(frame, track_id):
    name = f"evidence/{track_id}_{datetime.now().strftime('%H%M%S')}.jpg"
    cv2.imwrite(name, frame)
