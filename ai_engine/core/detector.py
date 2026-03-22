from ultralytics import YOLO
import torch


class Detector:
    def __init__(self, model_path="ai_engine/models/yolov8s.pt"):
        # ✅ Device setup
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # ✅ Load model
        self.model = YOLO(model_path)

        # ✅ Set device once (cleaner)
        self.model.to(self.device)

        # ✅ Enable FP16 for GPU (BIG speed boost)
        self.use_fp16 = self.device == "cuda"

        # ✅ Speed optimization
        torch.backends.cudnn.benchmark = True

        # ✅ Cache class names (avoid repeated lookup)
        self.class_names = self.model.names

        # ✅ Allowed classes
        self.allowed_classes = {
            "person",
            "car",
            "motorcycle",
            "bus",
            "truck",
            "bicycle"
        }

        print(f"[INFO] Detector initialized on {self.device}")

    def detect(self, frame):
        """
        Run detection on a frame
        """

        with torch.no_grad():
            results = self.model(
                frame,
                conf=0.4,
                imgsz=640,
                device=self.device,
                half=self.use_fp16,   # ✅ FP16 acceleration
                verbose=False
            )

        detections = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls_id = int(box.cls[0])
                cls_name = self.class_names[cls_id]

                # ✅ Filter classes
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