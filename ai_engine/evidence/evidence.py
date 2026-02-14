import cv2
from datetime import datetime
import os

BASE_DIR = "ai_engine/evidence/output"
os.makedirs(BASE_DIR, exist_ok=True)

def save_violation(frame, track_id):
    import requests
    import time
    from datetime import datetime
    import cv2
    import os

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    img_path = f"ai_engine/evidence/output/{track_id}_{int(time.time())}.jpg"
    cv2.imwrite(img_path, frame)

    payload = {
        "time": ts,
        "camera_id": "CAM_DEMO",
        "vehicle_type": "Unknown",
        "violation_type": "Speed",
        "speed": 0,
        "image_path": img_path,
        "confidence": 0.9,
        "track_id": str(track_id)
    }

    try:
        requests.post(
            "http://127.0.0.1:8000/report_violation",
            json=payload,
            timeout=0.5
        )
    except:
        pass  # NEVER break AI loop