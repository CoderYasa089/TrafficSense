import time


class RuleEngine:
    def __init__(self):
        # Track object history
        self.object_history = {}

        # -------------------------------
        # CONFIG (🔥 FINAL TUNED)
        # -------------------------------
        self.min_frames = 2

        # 🔥 Based on your logs (max ≈ 28)
        self.speed_threshold = 18   # ✅ PERFECT VALUE

        self.speed_buffer_size = 3

        self.violation_counter = 1
        self.violated_ids = {}
        self.red_timer = {}

        # 🔥 Make RED clearly visible
        self.red_duration = 120  # ~4 sec

        self.vehicle_classes = {"car", "bus", "truck", "motorcycle"}

    def update(self, tracked_objects):
        results = []

        for obj in tracked_objects:
            obj_id = obj["id"]

            # -------------------------------
            # INIT OBJECT
            # -------------------------------
            if obj_id not in self.object_history:
                self.object_history[obj_id] = {
                    "frames": 1,
                    "speed_buffer": []
                }

                obj["status"] = "OK"
                results.append(obj)
                continue

            history = self.object_history[obj_id]
            history["frames"] += 1

            # -------------------------------
            # SPEED PROCESSING
            # -------------------------------
            speed = obj.get("speed", 0)

            history["speed_buffer"].append(speed)
            if len(history["speed_buffer"]) > self.speed_buffer_size:
                history["speed_buffer"].pop(0)

            avg_speed = sum(history["speed_buffer"]) / len(history["speed_buffer"])

            # -------------------------------
            # IGNORE VERY EARLY FRAMES
            # -------------------------------
            if history["frames"] < self.min_frames:
                obj["status"] = "OK"
                results.append(obj)
                continue

            # -------------------------------
            # RULE: OVERSPEED
            # -------------------------------
            is_vehicle = obj["class"] in self.vehicle_classes
            is_overspeed = avg_speed > self.speed_threshold

            # 🔥 IMPORTANT DEBUG (keep for now)
            print(f"[DEBUG] ID {obj_id} speed={avg_speed}")

            if is_vehicle and is_overspeed:

                print(f"[VIOLATION] ID {obj_id} speed={avg_speed}")

                # FIRST TIME VIOLATION
                if obj_id not in self.violated_ids:
                    vid = self.violation_counter
                    self.violation_counter += 1

                    self.violated_ids[obj_id] = vid
                    self.red_timer[obj_id] = self.red_duration

                vid = self.violated_ids[obj_id]

                obj["violation_id"] = vid
                obj["violation_type"] = "overspeed"
                obj["speed"] = int(avg_speed)

                # RED → YELLOW
                if self.red_timer.get(obj_id, 0) > 0:
                    obj["status"] = "VIOLATION_RED"
                else:
                    obj["status"] = "VIOLATION_YELLOW"

            else:
                if obj_id in self.violated_ids:
                    obj["violation_id"] = self.violated_ids[obj_id]
                    obj["status"] = "VIOLATION_YELLOW"
                else:
                    obj["status"] = "OK"

            results.append(obj)

        # -------------------------------
        # TIMER UPDATE
        # -------------------------------
        for obj_id in list(self.red_timer.keys()):
            self.red_timer[obj_id] -= 1
            if self.red_timer[obj_id] <= 0:
                del self.red_timer[obj_id]

        return results