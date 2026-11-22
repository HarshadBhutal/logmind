
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from main import app
from controllers import ingestion_controller


client = TestClient(app)


def valid_batch():
    return {
        "events": [
            {
                "level": "ERROR",
                "message": "Database connection timeout",
                "service": "payment-service",
                "environment": "development",
                "source": "file",
                "request_id": "req-123",
                "attributes": {
                    "error_code": "DB_TIMEOUT"
                }
            },
            {
                "level": "INFO",
                "message": "Payment service started",
                "service": "payment-service",
                "environment": "development",
                "source": "file"
            }
        ]
    }


def test_successful_batch_ingestion(monkeypatch):

    mock_ingest = AsyncMock(
        return_value={
            "accepted": 2,
            "failed": 0,
            "errors": []
        }
    )

    monkeypatch.setattr(
        ingestion_controller,
        "ingest_logs",
        mock_ingest
    )

    response = client.post(
        "/api/v1/ingest",
        json=valid_batch()
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 2
    assert response.json()["failed"] == 0

    mock_ingest.assert_awaited_once()


def test_invalid_log_level():

    payload = valid_batch()
    payload["events"][0]["level"] = "INVALID"

    response = client.post(
        "/api/v1/ingest",
        json=payload
    )

    assert response.status_code == 422


def test_empty_batch():

    response = client.post(
        "/api/v1/ingest",
        json={"events": []}
    )

    assert response.status_code == 422


def test_batch_exceeding_limit():

    payload = {
        "events": [
            {
                "level": "INFO",
                "message": "Test log",
                "service": "test-service"
            }
            for _ in range(501)
        ]
    }

    response = client.post(
        "/api/v1/ingest",
        json=payload
    )

    assert response.status_code == 422


def test_elasticsearch_transport_failure(monkeypatch):

    from elasticsearch.exceptions import TransportError

    mock_ingest = AsyncMock(
        side_effect=TransportError("Connection failed")
    )

    monkeypatch.setattr(
        ingestion_controller,
        "ingest_logs",
        mock_ingest
    )

    response = client.post(
        "/api/v1/ingest",
        json=valid_batch()
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Log ingestion service is temporarily unavailable"
    )
