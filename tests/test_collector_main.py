
import pytest

from collector.main import LogCollector


@pytest.mark.anyio
async def test_valid_log_lines_are_added_to_buffer(monkeypatch):
    collector = LogCollector()
    collector.running = True

    async def mock_read_lines():
        yield "2026-11-24 10:30:00 INFO Application started"

    monkeypatch.setattr(
        collector.reader,
        "read_lines",
        mock_read_lines
    )

    await collector.collect_logs()

    assert collector.buffer.size == 1

    event = collector.buffer.peek_batch(1)[0]
    assert event["level"] == "INFO"
    assert event["message"] == "Application started"

    await collector.exporter.close()


@pytest.mark.anyio
async def test_invalid_log_lines_are_skipped(monkeypatch):
    collector = LogCollector()
    collector.running = True

    async def mock_read_lines():
        yield "This is not a valid log line"

    monkeypatch.setattr(
        collector.reader,
        "read_lines",
        mock_read_lines
    )

    await collector.collect_logs()

    assert collector.buffer.size == 0

    await collector.exporter.close()


@pytest.mark.anyio
async def test_successful_export_acknowledges_events(monkeypatch):
    collector = LogCollector()
    collector.running = True

    collector.buffer.add({
        "level": "INFO",
        "message": "Application started"
    })

    async def mock_send_batch(events):
        collector.running = False
        return True

    monkeypatch.setattr(
        collector.exporter,
        "send_batch",
        mock_send_batch
    )

    await collector.export_logs()

    assert collector.buffer.size == 0

    await collector.exporter.close()


@pytest.mark.anyio
async def test_failed_export_keeps_events(monkeypatch):
    collector = LogCollector()
    collector.running = True

    event = {
        "level": "ERROR",
        "message": "Database connection failed"
    }

    collector.buffer.add(event)

    async def mock_send_batch(events):
        collector.running = False
        return False

    async def mock_sleep(delay):
        pass

    monkeypatch.setattr(
        collector.exporter,
        "send_batch",
        mock_send_batch
    )
    monkeypatch.setattr(
        "collector.main.asyncio.sleep",
        mock_sleep
    )

    await collector.export_logs()

    assert collector.buffer.peek_batch(1) == [event]
    assert collector.buffer.size == 1

    await collector.exporter.close()


@pytest.mark.anyio
async def test_stop_triggers_shutdown():
    collector = LogCollector()

    await collector.stop()

    assert collector.shutdown_event.is_set()


@pytest.mark.anyio
async def test_flush_buffer_acknowledges_successful_delivery(monkeypatch):
    collector = LogCollector()

    event = {
        "level": "INFO",
        "message": "Application started"
    }

    collector.buffer.add(event)

    async def mock_send_batch(events):
        return True

    monkeypatch.setattr(
        collector.exporter,
        "send_batch",
        mock_send_batch
    )

    await collector.flush_buffer()

    assert collector.buffer.size == 0

    await collector.exporter.close()
