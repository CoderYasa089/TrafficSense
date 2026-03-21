import math

class Tracker:
    def __init__(self, max_distance=50):
        self.next_id = 0
        self.objects = {}  # id -> {centroid, positions}
        self.max_distance = max_distance

    def _get_centroid(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _distance(self, c1, c2):
        return math.hypot(c1[0] - c2[0], c1[1] - c2[1])

    def update(self, detections):
        updated_objects = {}
        results = []

        used_ids = set()

        for det in detections:
            centroid = self._get_centroid(det["bbox"])

            best_id = None
            min_dist = float("inf")

            # 🔥 Find closest match (FIXED)
            for obj_id, obj_data in self.objects.items():
                if obj_id in used_ids:
                    continue

                dist = self._distance(centroid, obj_data["centroid"])

                if dist < self.max_distance and dist < min_dist:
                    min_dist = dist
                    best_id = obj_id

            # Assign ID
            if best_id is None:
                obj_id = self.next_id
                self.next_id += 1
                obj_data = {"centroid": centroid, "positions": [centroid]}
            else:
                obj_id = best_id
                obj_data = self.objects[obj_id]
                obj_data["centroid"] = centroid
                obj_data["positions"].append(centroid)

                if len(obj_data["positions"]) > 5:
                    obj_data["positions"].pop(0)

            used_ids.add(obj_id)

            # 🔥 Stable speed
            if len(obj_data["positions"]) >= 2:
                x1, y1 = obj_data["positions"][0]
                x2, y2 = obj_data["positions"][-1]
                speed = abs(x2 - x1) + abs(y2 - y1)
            else:
                speed = 0

            updated_objects[obj_id] = obj_data

            det["id"] = obj_id
            det["speed"] = speed
            results.append(det)

        self.objects = updated_objects
        return results