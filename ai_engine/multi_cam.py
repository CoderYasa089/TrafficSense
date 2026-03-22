import threading
from ai_engine.main_engine import TrafficEngine


def run_camera(video_path):
    print(f"[INFO] Starting camera: {video_path}")
    engine = TrafficEngine(video_path)
    engine.run()


if __name__ == "__main__":
    video_list = [
        "data/videos/traffic1.mp4",
        "data/videos/traffic3.mp4",
        "data/videos/traffic4.mp4"
    ]

    threads = []

    for video in video_list:
        t = threading.Thread(target=run_camera, args=(video,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("[INFO] All cameras finished")