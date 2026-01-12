from deep_sort_realtime.deepsort_tracker import DeepSort

tracker = DeepSort(max_age=30)

def track(detections, frame):
    return tracker.update_tracks(detections, frame=frame)
