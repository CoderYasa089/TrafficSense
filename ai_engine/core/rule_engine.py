import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self):
        self.object_history = {}

        self.min_frames = 2
        self.speed_threshold = 18
        self.speed_buffer_size = 3

        self.violation_counter = 1
        self.violated_ids = {}
        self.red_timer = {}
        self.red_duration = 120

        self.vehicle_classes = {"car", "bus", "truck", "motorcycle"}

    def update(self, tracked_objects):
        results = []

        for obj in tracked_objects:
            obj_id = obj["id"]

            if obj_id not in self.object_history:
                self.object_history[obj_id] = {
                    "frames": 1,
                    "speed_buffer": [],
                }

                obj["status"] = "OK"
                results.append(obj)
                continue

            history = self.object_history[obj_id]
            history["frames"] += 1

            speed = obj.get("speed", 0)

            history["speed_buffer"].append(speed)
            if len(history["speed_buffer"]) > self.speed_buffer_size:
                history["speed_buffer"].pop(0)

            avg_speed = sum(history["speed_buffer"]) / len(history["speed_buffer"])

            if history["frames"] < self.min_frames:
                obj["status"] = "OK"
                results.append(obj)
                continue

            is_vehicle = obj["class"] in self.vehicle_classes
            is_overspeed = avg_speed > self.speed_threshold

            if is_vehicle and is_overspeed:
                logger.debug(f"Violation detected: id={obj_id}, speed={avg_speed:.2f}")

                if obj_id not in self.violated_ids:
                    vid = self.violation_counter
                    self.violation_counter += 1

                    self.violated_ids[obj_id] = vid
                    self.red_timer[obj_id] = self.red_duration

                vid = self.violated_ids[obj_id]

                obj["violation_id"] = vid
                obj["violation_type"] = "overspeed"
                obj["speed"] = int(avg_speed)

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

        for obj_id in list(self.red_timer.keys()):
            self.red_timer[obj_id] -= 1
            if self.red_timer[obj_id] <= 0:
                del self.red_timer[obj_id]

        return results