
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


LogLevel = Literal[
    "TRACE",
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


class LogEvent(BaseModel):
    """
    Standard log event format used throughout LogMind.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    level: LogLevel

    message: str = Field(
        min_length=1,
        max_length=10000,
    )

    service: str = Field(
        min_length=1,
        max_length=128,
    )

    environment: str = Field(
        default="development",
        max_length=64,
    )

    source: Literal["file", "docker", "otlp", "api"] = "file"

    request_id: str | None = Field(
        default=None,
        max_length=128,
    )

    trace_id: str | None = Field(
        default=None,
        max_length=128,
    )

    span_id: str | None = Field(
        default=None,
        max_length=128,
    )

    host: str | None = Field(
        default=None,
        max_length=255,
    )

    attributes: dict[str, Any] = Field(
        default_factory=dict
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must include timezone information")

        return value.astimezone(timezone.utc)




class BatchLogRequest(BaseModel):
    events: list[LogEvent] = Field(
        min_length=1,
        max_length=500
    )


class IngestionResponse(BaseModel):
    accepted: int
    failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)