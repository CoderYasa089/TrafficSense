from queue import Queue, Empty
import threading
import cv2

from ai_engine.core.detector import Detector
from ai_engine.core.tracker import Tracker
from ai_engine.core.rule_engine import RuleEngine
from ai_engine.utils.api_client import send_violation
from ai_engine.evidence.evidence import save_violation_image


class TrafficEngine:
    def __init__(self, video_path):
        self.video_path = video_path

        # ✅ CLEAN NAMES
        self.video_name = self.video_path.split("/")[-1]
        self.camera_id = self.video_name.replace(".mp4", "").upper()
        self.window_name = f"CAMERA - {self.camera_id}"

        print(f"[INFO] Initializing Detector for {video_path}...")
        self.detector = Detector()

        print(f"[INFO] Initializing Tracker for {video_path}...")
        self.tracker = Tracker()

        print(f"[INFO] Initializing Rule Engine for {video_path}...")
        self.rule_engine = RuleEngine()

        self.sent_violations = set()

        # ✅ Queue system
        self.api_queue = Queue()
        self.api_worker_running = True

    # -------------------------------
    # API WORKER
    # -------------------------------
    def api_worker(self):
        while self.api_worker_running:
            try:
                obj, image_path = self.api_queue.get(timeout=1)

                response = send_violation(obj, image_path)
                print(f"[API RESPONSE - {self.camera_id}]", response)

                self.api_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                print(f"[API ERROR - {self.camera_id}]", e)

    # -------------------------------
    # MAIN LOOP
    # -------------------------------
    def run(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print(f"[ERROR] Cannot open video: {self.video_path}")
            return

        # ✅ Start API worker
        threading.Thread(target=self.api_worker, daemon=True).start()

        # ✅ Window setup
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        WIDTH = 640
        HEIGHT = 360
        cv2.resizeWindow(self.window_name, WIDTH, HEIGHT)

        # ✅ GRID POSITIONS
        positions = {
            "traffic1.mp4": (0, 0),
            "traffic3.mp4": (WIDTH + 10, 0),
            "traffic4.mp4": (0, HEIGHT + 40),
            "traffic5.mp4": (WIDTH + 10, HEIGHT + 40),
        }

        if self.video_name in positions:
            x, y = positions[self.video_name]
            cv2.moveWindow(self.window_name, x, y)

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30

        frame_count = 0

        print(f"[INFO] Processing started: {self.camera_id}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # ✅ FPS optimization
            if frame_count % 2 != 0:
                continue

            video_time = frame_count / fps

            # -------------------------------
            # PIPELINE
            # -------------------------------
            detections = self.detector.detect(frame)
            tracked_objects = self.tracker.update(detections)
            processed_objects = self.rule_engine.update(tracked_objects)

            # -------------------------------
            # VISUALIZATION + LOGIC
            # -------------------------------
            for obj in processed_objects:
                x1, y1, x2, y2 = obj["bbox"]

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
                cv2.putText(
                    frame,
                    label,
                    (x1, y_text),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )

                # -------------------------------
                # SEND ONLY NEW VIOLATIONS
                # -------------------------------
                if obj["status"] == "VIOLATION_RED" and "violation_id" in obj:
                    vid = obj["violation_id"]

                    if vid not in self.sent_violations:
                        self.sent_violations.add(vid)

                        image_path = save_violation_image(frame.copy(), obj)

                        # 🔥 IMPORTANT FIXES
                        obj["video_time"] = round(video_time, 2)
                        obj["camera_id"] = self.camera_id

                        # ✅ Send via queue
                        self.api_queue.put((obj.copy(), image_path))

            # -------------------------------
            # DISPLAY
            # -------------------------------
            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:
                break

            # ✅ Window close detection
            try:
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except:
                break

        # -------------------------------
        # CLEAN EXIT
        # -------------------------------
        self.api_worker_running = False
        cap.release()

        try:
            cv2.destroyWindow(self.window_name)
        except:
            pass

        print(f"[INFO] Camera stopped: {self.camera_id}")


# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    video_path = "data/videos/traffic5.mp4"

    engine = TrafficEngine(video_path)
    engine.run()