def start_video_engine(video_path):
    import cv2
    import time
    from ultralytics import YOLO
    from ai_engine.tracking.tracker import track
    from ai_engine.logic.violation import check_speed, reset_violation_state
    from ai_engine.evidence.evidence import save_violation

    ALLOWED_CLASSES = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    # FIX 3: reset state per video
    reset_violation_state()

    model = YOLO("ai_engine/models/yolov8m.pt")
    cap = cv2.VideoCapture(video_path)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=0.4)[0]
        detections = []

        for box in results.boxes:
            cls = int(box.cls[0])
            if cls not in ALLOWED_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            w, h = x2 - x1, y2 - y1
            detections.append(([x1, y1, w, h], conf, cls))

        tracks = track(detections, frame)
        now = time.time()

        for t in tracks:
            if not t.is_confirmed():
                continue

            track_id = t.track_id
            l, t0, r, b = map(int, t.to_ltrb())
            center_x = l + (r - l) // 2

            violated, speed = check_speed(track_id, center_x, now)

            if violated:
                save_violation(frame, track_id)
                cv2.putText(
                    frame,
                    "VIOLATION",
                    (l, t0 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

            # ALWAYS draw bounding box
            cv2.rectangle(frame, (l, t0), (r, b), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"ID {track_id}",
                (l, t0 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

        cv2.imshow("TrafficSense Offline", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or cv2.getWindowProperty(
            "TrafficSense Offline", cv2.WND_PROP_VISIBLE
        ) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
