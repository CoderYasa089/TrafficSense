import threading
import time
import logging

from ai_engine.main_engine import TrafficEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_camera(video_path):
    try:
        logger.info(f"Starting camera: {video_path}")

        engine = TrafficEngine(video_path)
        engine.run()

        logger.info(f"Camera finished: {video_path}")

    except Exception as e:
        logger.error(f"Camera failed ({video_path}): {e}")


if __name__ == "__main__":
    video_list = [
        "data/videos/traffic5.mp4",
        "data/videos/traffic3.mp4",
        "data/videos/traffic1.mp4",
    ]

    threads = []

    try:
        for video in video_list:
            t = threading.Thread(target=run_camera, args=(video,), daemon=True)
            t.start()
            threads.append(t)

        while any(t.is_alive() for t in threads):
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping all cameras")

    logger.info("All cameras finished")