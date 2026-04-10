import math


class Tracker:
    def __init__(self, max_distance=50, max_lost=5):
        self.next_id = 0
        self.objects = {}  # id -> {centroid, positions, lost}
        self.max_distance = max_distance
        self.max_lost = max_lost

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

            for obj_id, obj_data in self.objects.items():
                if obj_id in used_ids:
                    continue

                dist = self._distance(centroid, obj_data["centroid"])

                if dist < self.max_distance and dist < min_dist:
                    min_dist = dist
                    best_id = obj_id

            if best_id is None:
                obj_id = self.next_id
                self.next_id += 1

                obj_data = {
                    "centroid": centroid,
                    "positions": [centroid],
                    "lost": 0,
                }
            else:
                obj_id = best_id
                obj_data = self.objects[obj_id]

                obj_data["centroid"] = centroid
                obj_data["positions"].append(centroid)
                obj_data["lost"] = 0

                if len(obj_data["positions"]) > 5:
                    obj_data["positions"].pop(0)

            used_ids.add(obj_id)
            updated_objects[obj_id] = obj_data

            if len(obj_data["positions"]) >= 2:
                positions = obj_data["positions"]
                total_dist = 0

                for i in range(1, len(positions)):
                    total_dist += self._distance(positions[i - 1], positions[i])

                speed = total_dist / len(positions)
            else:
                speed = 0

            det["id"] = obj_id
            det["speed"] = int(speed)

            results.append(det)

        for obj_id, obj_data in self.objects.items():
            if obj_id not in updated_objects:
                obj_data["lost"] += 1

                if obj_data["lost"] <= self.max_lost:
                    updated_objects[obj_id] = obj_data

        self.objects = updated_objects

        return results