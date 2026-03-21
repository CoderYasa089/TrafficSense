from ultralytics import YOLO
import torch

class Detector:
    def __init__(self, model_path="ai_engine/models/yolov8s.pt"):
        # Load model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(model_path)

        # Move model to GPU
        self.model.to(self.device)

        # Allowed classes (reduce false detections)
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
        """
        Run detection on a frame
        """
        results = self.model(
            frame,
            device=self.device,
            conf=0.4,
            stream=False
        )

        detections = []

        for r in results:
            boxes = r.boxes

            for box in boxes:
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