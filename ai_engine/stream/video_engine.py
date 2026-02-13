def start_video_engine(video_path):
    import cv2
    import time
    from ultralytics import YOLO
    from ai_engine.tracking.tracker import track
    from ai_engine.logic.violation import check_speed, reset_violation_state
    from ai_engine.evidence.evidence import save_violation

    ALLOWED_CLASSES = [2, 3, 5, 7]

    reset_violation_state()  # 🔑 FIX 3

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

        cv2.imshow("TrafficSense Offline", frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
