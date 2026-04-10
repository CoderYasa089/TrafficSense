from ultralytics import YOLO
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Detector:
    def __init__(self, model_path="ai_engine/models/yolov8s.pt"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = YOLO(model_path)
        self.model.to(self.device)

        self.use_fp16 = self.device == "cuda"

        torch.backends.cudnn.benchmark = True

        self.class_names = self.model.names

        self.allowed_classes = {
            "person",
            "car",
            "motorcycle",
            "bus",
            "truck",
            "bicycle",
        }

        logger.info(f"Detector initialized on {self.device}")

    def detect(self, frame):
        with torch.no_grad():
            results = self.model(
                frame,
                conf=0.4,
                imgsz=640,
                device=self.device,
                half=self.use_fp16,
                verbose=False,
            )

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.class_names[cls_id]

                if cls_name not in self.allowed_classes:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                detections.append(
                    {
                        "class": cls_name,
                        "confidence": conf,
                        "bbox": (x1, y1, x2, y2),
                    }
                )

        return detections