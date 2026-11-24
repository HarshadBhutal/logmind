
import json
import re
from datetime import datetime, timezone
from typing import Any

from collector.config import settings


LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} "
    r"\d{2}:\d{2}:\d{2}) "
    r"(?P<level>TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL) "
    r"(?P<message>.*)$",
    re.IGNORECASE
)


class LogParser:

    def parse(self, raw_line: str) -> dict[str, Any] | None:

        try:
            event = json.loads(raw_line)

            if not isinstance(event, dict):
                return None

            return self._normalize(event)

        except json.JSONDecodeError:
            return self._parse_text(raw_line)

    def _parse_text(self, raw_line: str) -> dict[str, Any] | None:

        match = LOG_PATTERN.match(raw_line)

        if not match:
            return None

        try:
            timestamp = datetime.strptime(
                match.group("timestamp"),
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

        except ValueError:
            return None

        return self._normalize({
            "timestamp": timestamp.isoformat(),
            "level": match.group("level").upper(),
            "message": match.group("message")
        })

    def _normalize(self, event: dict[str, Any]) -> dict[str, Any] | None:

        level = str(event.get("level", "INFO")).upper()

        allowed_levels = {
            "TRACE", "DEBUG", "INFO",
            "WARNING", "ERROR", "CRITICAL"
        }

        message = event.get("message")

        if level not in allowed_levels:
            return None

        if not isinstance(message, str) or not message.strip():
            return None

        timestamp = event.get("timestamp")

        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        event["timestamp"] = timestamp
        event["level"] = level
        event["message"] = message.strip()
        event["service"] = event.get(
            "service",
            settings.SERVICE_NAME
        )
        event["environment"] = event.get(
            "environment",
            settings.ENVIRONMENT
        )
        event["source"] = "file"

        return event
