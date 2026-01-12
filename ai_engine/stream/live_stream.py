import cv2
from ultralytics import YOLO

model = YOLO("ai_engine/models/yolov8m.pt")

cap = cv2.VideoCapture(0)  # webcam; later IP camera

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, stream=True)

    for r in results:
        annotated = r.plot()
        cv2.imshow("TrafficSense Live", annotated)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
