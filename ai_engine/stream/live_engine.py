import cv2
from ultralytics import YOLO
from ai_engine.tracking.tracker import track
from ai_engine.logic.violation import check_speed
from ai_engine.evidence.evidence import save_violation

model = YOLO("ai_engine/models/yolov8m.pt")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)[0]

    detections = []
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        cls = int(box.cls[0])
        detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls))

    tracks = track(detections, frame)

    for t in tracks:
        if not t.is_confirmed():
            continue

        track_id = t.track_id
        l, t0, w, h = map(int, t.to_ltrb())
        center_x = l + w // 2

        violated, speed = check_speed(track_id, center_x)

        if violated:
            save_violation(frame, track_id)
            cv2.putText(frame, f"VIOLATION {track_id}", (l, t0 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        cv2.rectangle(frame, (l, t0), (l + w, t0 + h), (0,255,0), 2)
        cv2.putText(frame, f"ID {track_id}", (l, t0 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

    cv2.imshow("TrafficSense Engine", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
