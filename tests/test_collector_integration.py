
import asyncio

import httpx
import pytest

from collector.buffer import LogBuffer
from collector.exporter import LogExporter
from collector.parser import LogParser
from collector.reader import FileReader


@pytest.mark.anyio
async def test_complete_collector_pipeline(tmp_path, monkeypatch):
    # Create a temporary log file.
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2026-11-24 10:30:00 INFO Application started\n",
        encoding="utf-8"
    )

    # Read existing log lines during this test.
    monkeypatch.setattr(
        "collector.reader.settings.READ_FROM_START",
        True
    )

    # Initialize collector components.
    reader = FileReader(log_file)
    parser = LogParser()
    buffer = LogBuffer(capacity=100)
    exporter = LogExporter()

    received_payloads = []

    async def mock_post(url, json):
        received_payloads.append(json)

        return httpx.Response(
            200,
            json={
                "accepted": len(json["events"]),
                "failed": 0,
                "errors": []
            },
            request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(exporter.client, "post", mock_post)

    try:
        # Read and parse a log line.
        lines = reader.read_lines()

        raw_line = await anext(lines)
        event = parser.parse(raw_line)

        assert event is not None

        # Add event to the buffer.
        assert buffer.add(event)

        # Export the buffered event.
        batch = buffer.peek_batch(10)
        success = await exporter.send_batch(batch)

        assert success is True

        # Acknowledge successful delivery.
        buffer.acknowledge(len(batch))

        # Verify the entire pipeline.
        assert len(received_payloads) == 1
        assert received_payloads[0]["events"][0]["level"] == "INFO"
        assert received_payloads[0]["events"][0]["message"] == "Application started"
        assert buffer.size == 0

        await lines.aclose()

    finally:
        await exporter.close()
