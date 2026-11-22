
import pytest
from pydantic import ValidationError

from ingestion.schemas import LogEvent


def test_valid_log_event():

    event = LogEvent(
        level="ERROR",
        message="Database connection timeout",
        service="payment-service",
        environment="development",
        source="file",
        request_id="req-123",
        attributes={
            "error_code": "DB_TIMEOUT",
            "database": "mysql",
            "retry_count": 3,
        },
    )

    assert event.level == "ERROR"
    assert event.service == "payment-service"
    assert event.attributes["error_code"] == "DB_TIMEOUT"


def test_invalid_log_level():

    with pytest.raises(ValidationError):
        LogEvent(
            level="INVALID",
            message="Test error",
            service="payment-service",
        )


def test_empty_message():

    with pytest.raises(ValidationError):
        LogEvent(
            level="ERROR",
            message="",
            service="payment-service",
        )


def test_timestamp_must_have_timezone():

    with pytest.raises(ValidationError):
        LogEvent(
            timestamp="2026-11-22T10:30:00",
            level="INFO",
            message="Test message",
            service="test-service",
        )
