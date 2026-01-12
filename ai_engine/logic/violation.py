import time

speed_memory = {}

def check_speed(track_id, position):
    now = time.time()

    if track_id in speed_memory:
        prev_pos, prev_time = speed_memory[track_id]
        speed = abs(position - prev_pos) / (now - prev_time)
        if speed > 12:
            return True, speed

    speed_memory[track_id] = (position, now)
    return False, 0
