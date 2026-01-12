# ai_engine/logic/frame_buffer.py
from collections import deque

class FrameBuffer:
    def __init__(self, size=30):
        self.buffer = deque(maxlen=size)

    def push(self, frame):
        self.buffer.append(frame)

    def pop(self):
        if self.buffer:
            return self.buffer.popleft()
