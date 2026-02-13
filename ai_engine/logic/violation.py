# ai_engine/logic/violation.py

import time

MIN_HISTORY = 3          # 🔑 warm-up frames
SPEED_THRESHOLD = 150    # tune later

speed_memory = {}        # { track_id: [(pos, time), ...] }
violation_count = {}     # { track_id: count }

def check_speed(track_id, position, current_time):
    # Initialize memory
    if track_id not in speed_memory:
        speed_memory[track_id] = []
        violation_count[track_id] = 0
        return False, 0

    # Append history
    speed_memory[track_id].append((position, current_time))

    # 🔒 FIX 1: Warm-up phase
    if len(speed_memory[track_id]) < MIN_HISTORY:
        return False, 0

    # Use last two points only
    prev_pos, prev_time = speed_memory[track_id][-2]
    curr_pos, curr_time = speed_memory[track_id][-1]

    dt = curr_time - prev_time
    if dt <= 0:
        return False, 0

    speed = abs(curr_pos - prev_pos) / dt

    # Count violations temporally
    if speed > SPEED_THRESHOLD:
        violation_count[track_id] += 1
    else:
        violation_count[track_id] = 0

    # 🔒 FIX 4 applied here (temporal confirmation)
    if violation_count[track_id] >= 3:
        return True, speed

    return False, speed

def reset_violation_state():
    speed_memory.clear()
    violation_count.clear()
