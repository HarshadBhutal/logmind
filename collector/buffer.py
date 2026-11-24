
from collections import deque
from typing import Any


class LogBuffer:

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Buffer capacity must be positive")

        self.capacity = capacity
        self.events: deque[dict[str, Any]] = deque()
        self.dropped = 0

    def add(self, event: dict[str, Any]) -> bool:

        if len(self.events) >= self.capacity:
            self.dropped += 1
            return False

        self.events.append(event)
        return True

    def peek_batch(self, batch_size: int) -> list[dict[str, Any]]:

        if batch_size <= 0:
            raise ValueError("Batch size must be positive")

        return list(self.events)[:batch_size]

    def acknowledge(self, count: int) -> None:

        if count < 0 or count > len(self.events):
            raise ValueError("Invalid acknowledgement count")

        for _ in range(count):
            self.events.popleft()

    @property
    def size(self) -> int:
        return len(self.events)
