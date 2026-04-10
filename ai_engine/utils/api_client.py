import requests
import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://127.0.0.1:8000/report_violation"


def send_violation(obj, image_path):
    if image_path is None:
        logger.warning("Skipping API call: no image provided")
        return None

    camera_id = obj.get("camera_id", "CAM_UNKNOWN")

    payload = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera_id": camera_id,
        "vehicle_type": obj.get("class"),
        "vehicle_subtype": None,
        "violation_type": obj.get("violation_type"),
        "speed": int(obj.get("speed", 0)),
        "image_path": image_path,
        "confidence": float(obj.get("confidence")) if obj.get("confidence") else None,
        "track_id": str(obj.get("id")),
        "plate_number": None,
        "video_time": obj.get("video_time"),
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=3,
        )

        if response.status_code == 200:
            return response.json()

        logger.error(f"API error: status={response.status_code}")
        return None

    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return None

    except requests.exceptions.ConnectionError:
        logger.error("Backend not reachable")
        return None

    except Exception as e:
        logger.error(f"Unexpected API error: {e}")
        return None