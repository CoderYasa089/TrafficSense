import cv2
import os
import datetime

OUTPUT_DIR = "data/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_violation_image(frame, obj):
    # ✅ Work on a copy
    frame_copy = frame.copy()

    x1, y1, x2, y2 = obj["bbox"]

    # ✅ Safe text position
    y_text = max(20, y1 - 10)

    label = f"{obj['class']} | VID {obj['violation_id']}"

    # Draw box + label
    cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(
        frame_copy,
        label,
        (x1, y_text),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        2
    )

    # ✅ Padding
    padding = 40

    h, w = frame.shape[:2]

    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)

    # ✅ Prevent invalid crop
    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame_copy[y1:y2, x1:x2]

    # ✅ Unique filename (prevents overwrite)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    filename = f"{obj['violation_id']}_{timestamp}.jpg"
    path = os.path.join(OUTPUT_DIR, filename)

    success = cv2.imwrite(path, crop)

    if not success:
        print("[ERROR] Failed to save image")
        return None

    return path