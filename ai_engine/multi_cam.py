import threading
import time
from ai_engine.main_engine import TrafficEngine


def run_camera(video_path):
    try:
        print(f"[INFO] Starting camera: {video_path}")
        engine = TrafficEngine(video_path)
        engine.run()
        print(f"[INFO] Camera finished: {video_path}")

    except Exception as e:
        print(f"[ERROR] Camera failed: {video_path} -> {e}")


if __name__ == "__main__":
    video_list = [
        "data/videos/traffic5.mp4",
        "data/videos/traffic3.mp4",
        "data/videos/traffic1.mp4"
    ]

    threads = []

    try:
        # ✅ Start all cameras
        for video in video_list:
            t = threading.Thread(target=run_camera, args=(video,), daemon=True)
            t.start()
            threads.append(t)

        # ✅ Keep main thread alive
        while any(t.is_alive() for t in threads):
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping all cameras...")

    print("[INFO] All cameras finished")