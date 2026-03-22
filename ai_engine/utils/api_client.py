import requests
import datetime

API_URL = "http://127.0.0.1:8000/report_violation"


def send_violation(obj, image_path):
    # -------------------------------
    # SAFETY CHECK
    # -------------------------------
    if image_path is None:
        print("[WARNING] Skipping API call (no image)")
        return None

    # -------------------------------
    # CAMERA ID FIX (🔥 IMPORTANT)
    # -------------------------------
    camera_id = obj.get("camera_id", "CAM_UNKNOWN")

    # -------------------------------
    # BUILD PAYLOAD
    # -------------------------------
    payload = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera_id": camera_id,  # ✅ FIXED (dynamic)
        "vehicle_type": obj.get("class"),
        "vehicle_subtype": None,
        "violation_type": obj.get("violation_type"),
        "speed": int(obj.get("speed", 0)),
        "image_path": image_path,
        "confidence": float(obj.get("confidence", 0)) if obj.get("confidence") else None,
        "track_id": str(obj.get("id")),
        "plate_number": None,
        "video_time": obj.get("video_time")
    }

    # -------------------------------
    # API CALL
    # -------------------------------
    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=3  # prevents freezing
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"[API ERROR] Status: {response.status_code}")
            return None

    # -------------------------------
    # ERROR HANDLING
    # -------------------------------
    except requests.exceptions.Timeout:
        print("[API ERROR] Request timeout")
        return None

    except requests.exceptions.ConnectionError:
        print("[API ERROR] Backend not running")
        return None

    except Exception as e:
        print("[API ERROR]", e)
        return None