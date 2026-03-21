from ultralytics import YOLO
import torch

class Detector:
    def __init__(self, model_path="ai_engine/models/yolov8s.pt"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(model_path)

        self.allowed_classes = [
            "person",
            "car",
            "motorcycle",
            "bus",
            "truck",
            "bicycle"
        ]

        print(f"[INFO] Detector initialized on {self.device}")

    def detect(self, frame):
        results = self.model(
            frame,
            conf=0.4,
            imgsz=640
        )

        detections = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names[cls_id]

                if cls_name not in self.allowed_classes:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                detections.append({
                    "class": cls_name,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2)
                })

        return detections