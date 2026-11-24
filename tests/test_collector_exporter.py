
import httpx
import pytest

from collector.exporter import LogExporter


@pytest.mark.anyio
async def test_successful_batch_delivery(monkeypatch):

    exporter = LogExporter()

    async def mock_post(url, json):
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
        result = await exporter.send_batch([
            {"level": "INFO", "message": "Test"}
        ])

        assert result is True

    finally:
        await exporter.close()


@pytest.mark.anyio
async def test_failed_batch_delivery(monkeypatch):

    exporter = LogExporter()

    async def mock_post(url, json):
        return httpx.Response(
            503,
            request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(exporter.client, "post", mock_post)

    try:
        result = await exporter.send_batch([
            {"level": "ERROR", "message": "Database failure"}
        ])

        assert result is False

    finally:
        await exporter.close()


@pytest.mark.anyio
async def test_empty_batch():

    exporter = LogExporter()

    try:
        result = await exporter.send_batch([])

        assert result is True

    finally:
        await exporter.close()
