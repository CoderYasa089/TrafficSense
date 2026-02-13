MODE = "video"   # "live" or "video"

VIDEO_FILES = [
    "datasets/videos/traffic1.mp4",
    "datasets/videos/traffic2.mp4"
]

def start_engine():
    if MODE == "live":
        from ai_engine.stream.live_engine import start_live_engine
        start_live_engine()

    elif MODE == "video":
        from ai_engine.stream.video_engine import start_video_engine

        for video in VIDEO_FILES:
            start_video_engine(video)

    else:
        print("Invalid MODE")

if __name__ == "__main__":
    start_engine()
