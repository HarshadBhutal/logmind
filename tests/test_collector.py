from collector.buffer import LogBuffer
from collector.parser import LogParser
from collector.reader import FileReader
import pytest

def test_buffer_acknowledgement():
    buffer = LogBuffer(capacity=5)

    first = {"message": "First"}
    second = {"message": "Second"}

    buffer.add(first)
    buffer.add(second)

    batch = buffer.peek_batch(2)

    assert batch == [first, second]
    assert buffer.size == 2

    buffer.acknowledge(2)

    assert buffer.size == 0


def test_failed_delivery_keeps_events():
    buffer = LogBuffer(capacity=5)

    event = {"message": "Test"}
    buffer.add(event)

    # Simulate failed delivery: do not acknowledge.
    batch = buffer.peek_batch(1)

    assert batch == [event]
    assert buffer.size == 1

    # The same event is available for another attempt.
    assert buffer.peek_batch(1) == [event]


def test_invalid_acknowledgement():
    buffer = LogBuffer(capacity=5)
    buffer.add({"message": "Test"})

    with pytest.raises(ValueError):
        buffer.acknowledge(2)
