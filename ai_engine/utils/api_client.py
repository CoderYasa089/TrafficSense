import requests
import datetime

API_URL = "http://127.0.0.1:8000/report_violation"

def send_violation(obj, image_path):
    payload = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera_id": "CAM_01",
        "vehicle_type": obj.get("class"),
        "vehicle_subtype": None,
        "violation_type": obj.get("violation_type"),
        "speed": obj.get("speed", 0),
        "image_path": image_path,
        "confidence": obj.get("confidence"),
        "track_id": str(obj.get("id")),
        "plate_number": None,
        "video_time": obj.get("video_time")  # 🔥 FIX
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=3   # 🔥 FIX (prevents freeze)
        )

        # 🔥 Check response
        if response.status_code == 200:
            return response.json()
        else:
            print("[ERROR] API status:", response.status_code)
            return None

    except Exception as e:
        print("[ERROR] API failed:", e)
        return None