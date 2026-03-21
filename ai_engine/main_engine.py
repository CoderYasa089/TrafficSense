import threading
from urllib import response

import cv2

from ai_engine.core.detector import Detector
from ai_engine.core.tracker import Tracker
from ai_engine.core.rule_engine import RuleEngine
from ai_engine.utils.api_client import send_violation
from ai_engine.evidence.evidence import save_violation_image

class TrafficEngine:
    def __init__(self, video_path):
        self.video_path = video_path

        print("[INFO] Initializing Detector...")
        self.detector = Detector()

        print("[INFO] Initializing Tracker...")
        self.tracker = Tracker()

        print("[INFO] Initializing Rule Engine...")
        self.rule_engine = RuleEngine()

        self.sent_violations = set()

    def run(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print("[ERROR] Cannot open video")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30
        frame_count = 0

        print("[INFO] Processing started...")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            video_time = frame_count / fps

            # Step 1: Detection
            detections = self.detector.detect(frame)

            # Step 2: Tracking
            tracked_objects = self.tracker.update(detections)

            # Step 3: Rule Engine
            processed_objects = self.rule_engine.update(tracked_objects)

            # Step 4: Visualization
            for obj in processed_objects:
                x1, y1, x2, y2 = obj["bbox"]
                obj_id = obj["id"]

                if obj["status"] == "VIOLATION_RED":
                    color = (0, 0, 255)
                    label = f"{obj['class']} | VID {obj['violation_id']} VIOLATION"

                elif obj["status"] == "VIOLATION_YELLOW":
                    color = (0, 255, 255)
                    label = f"{obj['class']} | VID {obj['violation_id']}"

                else:
                    color = (0, 255, 0)
                    label = f"{obj['class']} OK"

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                y_text = max(20, y1 - 10)

                cv2.putText(frame, label, (x1, y_text),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # SEND ONLY NEW VIOLATIONS
                if obj["status"] == "VIOLATION_RED" and "violation_id" in obj:
                    vid = obj.get("violation_id")

                    if vid not in self.sent_violations:
                        self.sent_violations.add(vid)

                    image_path = save_violation_image(frame.copy(), obj)

                    obj["video_time"] = round(video_time, 2)

                    import threading

                    def async_send(obj, image_path):
                        response = send_violation(obj, image_path)
                        print("[API RESPONSE]", response)

                    threading.Thread(target=async_send, args=(obj.copy(), image_path)).start()

                cv2.imshow("TrafficSense Engine", frame)

                key = cv2.waitKey(1)

                # ESC key
                if key == 27:
                    break

                # ❗ FIX: window close detection
                try:
                    if cv2.getWindowProperty("TrafficSense Engine", cv2.WND_PROP_VISIBLE) < 1:
                        break
                except:
                    break

        cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)

        print("[INFO] Processing completed")


# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    video_path = "data/videos/traffic1.mp4"

    engine = TrafficEngine(video_path)
    cv2.namedWindow("TrafficSense Engine", cv2.WINDOW_NORMAL)
    engine.run()