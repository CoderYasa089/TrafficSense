import cv2
from ai_engine.core.detector import Detector

detector = Detector()

cap = cv2.VideoCapture("data/videos/traffic1.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detections = detector.detect(frame)

    print(detections[:2])  # print sample

    cv2.imshow("Test", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()