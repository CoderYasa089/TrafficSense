import time

class RuleEngine:
    def __init__(self):
        # Track object history
        self.object_history = {}  # id -> {frames_seen, first_seen_time, last_position}

        # Config
        self.min_frames = 5  # ignore first few frames
        self.speed_threshold = 120  # pixels/frame (temporary logic)

        self.violation_counter = 1
        self.violated_ids = {}  # obj_id → VID
        self.red_timer = {}     # obj_id → frames left
        self.red_duration = 60  # ~2 sec

    def update(self, tracked_objects):
        results = []

        for obj in tracked_objects:
            obj_id = obj["id"]
            bbox = obj["bbox"]

            x1, y1, x2, y2 = bbox
            centroid = ((x1 + x2) // 2, (y1 + y2) // 2)

            # Initialize object history
            if obj_id not in self.object_history:
                self.object_history[obj_id] = {
                    "frames": 1,
                    "first_seen": time.time(),
                    "last_position": centroid
                }

                obj["status"] = "OK"
                results.append(obj)
                continue

            # Update history
            history = self.object_history[obj_id]
            history["frames"] += 1

            # ✅ Use tracker-computed stable speed (IMPORTANT FIX)
            speed = obj.get("speed", 0)

            # Keep updating last position (for future use if needed)
            history["last_position"] = centroid

            # Ignore early frames (IMPORTANT FIX)
            if history["frames"] < self.min_frames:
                obj["status"] = "OK"
                results.append(obj)
                continue

            # -------------------------------
            # RULE 1: OVERSPEED (BASIC)
            # -------------------------------
            if speed > self.speed_threshold and obj["class"] in ["car", "bus", "truck", "motorcycle"]:

                # FIRST TIME VIOLATION
                if obj_id not in self.violated_ids:
                    vid = self.violation_counter
                    self.violation_counter += 1

                    self.violated_ids[obj_id] = vid
                    self.red_timer[obj_id] = self.red_duration

                vid = self.violated_ids[obj_id]
                obj["violation_id"] = vid

                # RED PHASE
                if self.red_timer.get(obj_id, 0) > 0:
                    obj["status"] = "VIOLATION_RED"
                else:
                    obj["status"] = "VIOLATION_YELLOW"

                obj["violation_type"] = "overspeed"
                obj["speed"] = int(speed)

            else:
                # IMPORTANT: if already violated → STAY YELLOW
                if obj_id in self.violated_ids:
                    obj["violation_id"] = self.violated_ids[obj_id]
                    obj["status"] = "VIOLATION_YELLOW"
                else:
                    obj["status"] = "OK"

            results.append(obj)

        # Timer update
        for obj_id in list(self.red_timer.keys()):
            self.red_timer[obj_id] -= 1
            if self.red_timer[obj_id] <= 0:
                del self.red_timer[obj_id]

        return results