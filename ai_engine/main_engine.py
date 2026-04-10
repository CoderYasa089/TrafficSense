from queue import Queue, Empty
import threading
import cv2
import logging

from ai_engine.core.detector import Detector
from ai_engine.core.tracker import Tracker
from ai_engine.core.rule_engine import RuleEngine
from ai_engine.utils.api_client import send_violation
from ai_engine.evidence.evidence import save_violation_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrafficEngine:
    def __init__(self, video_path):
        self.video_path = video_path

        self.video_name = self.video_path.split("/")[-1]
        self.camera_id = self.video_name.replace(".mp4", "").upper()
        self.window_name = f"CAMERA - {self.camera_id}"

        logger.info(f"Initializing detector for {video_path}")
        self.detector = Detector()

        logger.info(f"Initializing tracker for {video_path}")
        self.tracker = Tracker()

        logger.info(f"Initializing rule engine for {video_path}")
        self.rule_engine = RuleEngine()

        self.sent_violations = set()

        self.api_queue = Queue()
        self.api_worker_running = True

    def api_worker(self):
        while self.api_worker_running:
            try:
                obj, image_path = self.api_queue.get(timeout=1)

                response = send_violation(obj, image_path)
                logger.info(f"API response ({self.camera_id}): {response}")

                self.api_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                logger.error(f"API worker error ({self.camera_id}): {e}")

    def run(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            logger.error(f"Cannot open video: {self.video_path}")
            return

        threading.Thread(target=self.api_worker, daemon=True).start()

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        width, height = 640, 360
        cv2.resizeWindow(self.window_name, width, height)

        positions = {
            "traffic1.mp4": (0, 0),
            "traffic3.mp4": (width + 10, 0),
            "traffic4.mp4": (0, height + 40),
            "traffic5.mp4": (width + 10, height + 40),
        }

        if self.video_name in positions:
            x, y = positions[self.video_name]
            cv2.moveWindow(self.window_name, x, y)

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = 0

        logger.info(f"Processing started: {self.camera_id}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            if frame_count % 2 != 0:
                continue

            video_time = frame_count / fps

            detections = self.detector.detect(frame)
            tracked_objects = self.tracker.update(detections)
            processed_objects = self.rule_engine.update(tracked_objects)

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
                    2,
                )

                if obj["status"] == "VIOLATION_RED" and "violation_id" in obj:
                    vid = obj["violation_id"]

                    if vid not in self.sent_violations:
                        self.sent_violations.add(vid)

                        image_path = save_violation_image(frame.copy(), obj)

                        obj["video_time"] = round(video_time, 2)
                        obj["camera_id"] = self.camera_id

                        self.api_queue.put((obj.copy(), image_path))

            cv2.imshow(self.window_name, frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:
                break

            try:
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                break

        self.api_worker_running = False
        cap.release()

        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            pass

        logger.info(f"Camera stopped: {self.camera_id}")


if __name__ == "__main__":
    video_path = "data/videos/traffic5.mp4"

    engine = TrafficEngine(video_path)
    engine.run()