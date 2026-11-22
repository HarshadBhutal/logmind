
import asyncio
from unittest.mock import AsyncMock

from ingestion.schemas import BatchLogRequest
from services import ingestion_service


def create_batch():
    return BatchLogRequest(
        events=[
            {
                "level": "ERROR",
                "message": "Database connection timeout",
                "service": "payment-service"
            },
            {
                "level": "INFO",
                "message": "Payment service started",
                "service": "payment-service"
            }
        ]
    )


def test_successful_bulk_insertion(monkeypatch):

    fake_es = object()

    mock_bulk = AsyncMock(
        return_value=(2, [])
    )

    monkeypatch.setattr(
        ingestion_service,
        "get_es",
        lambda: fake_es
    )

    monkeypatch.setattr(
        ingestion_service,
        "async_bulk",
        mock_bulk
    )

    result = asyncio.run(
        ingestion_service.ingest_logs(create_batch())
    )

    assert result["accepted"] == 2
    assert result["failed"] == 0
    assert result["errors"] == []

    mock_bulk.assert_awaited_once()

    # Verify that both events were passed to Elasticsearch.
    actions = mock_bulk.call_args.args[1]

    assert len(actions) == 2
    assert actions[0]["_index"] == "logmind-logs"


def test_partial_bulk_failure(monkeypatch):

    fake_es = object()

    bulk_errors = [
        {
            "index": {
                "_id": "failed-document-123",
                "error": {
                    "type": "mapper_parsing_exception",
                    "reason": "Invalid field value"
                }
            }
        }
    ]

    mock_bulk = AsyncMock(
        return_value=(1, bulk_errors)
    )

    monkeypatch.setattr(
        ingestion_service,
        "get_es",
        lambda: fake_es
    )

    monkeypatch.setattr(
        ingestion_service,
        "async_bulk",
        mock_bulk
    )

    result = asyncio.run(
        ingestion_service.ingest_logs(create_batch())
    )

    assert result["accepted"] == 1
    assert result["failed"] == 1

    assert result["errors"][0]["type"] == (
        "mapper_parsing_exception"
    )

    assert result["errors"][0]["reason"] == (
        "Invalid field value"
    )
