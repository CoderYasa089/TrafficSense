import cv2
from ai_engine.core.detector import Detector

detector = Detector()

cap = cv2.VideoCapture("data/videos/traffic1.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detections = detector.detect(frame)

    # DRAW BOUNDING BOXES
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = f"{det['class']} {det['confidence']:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Detection Test", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()