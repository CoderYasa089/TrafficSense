import cv2
import os
import datetime

OUTPUT_DIR = "data/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_violation_image(frame, obj):
    # 🔥 Work on a copy (IMPORTANT)
    frame_copy = frame.copy()

    x1, y1, x2, y2 = obj["bbox"]

    # 🔥 Safe text position
    y_text = max(20, y1 - 10)

    label = f"{obj['class']} | VID {obj['violation_id']}"

    # Draw box + label
    cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(frame_copy, label, (x1, y_text),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # 🔥 Padding
    padding = 40  # increased for better visibility

    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(frame.shape[1], x2 + padding)
    y2 = min(frame.shape[0], y2 + padding)

    crop = frame_copy[y1:y2, x1:x2]

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{obj['violation_id']}_{timestamp}.jpg"
    path = os.path.join(OUTPUT_DIR, filename)

    cv2.imwrite(path, crop)

    return path