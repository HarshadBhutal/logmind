
import asyncio
import logging
from typing import Any

import httpx

from collector.config import settings

logger = logging.getLogger(__name__)


class LogExporter:

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT
        )

    async def send_batch(
        self,
        events: list[dict[str, Any]]
    ) -> bool:

        if not events:
            return True

        payload = {"events": events}

        for attempt in range(settings.MAX_RETRIES + 1):

            try:
                response = await self.client.post(
                    settings.INGESTION_URL,
                    json=payload
                )

                response.raise_for_status()

                result = response.json()

                if result.get("failed", 0) > 0:
                    logger.error(
                        "Backend reported %s failed events",
                        result["failed"]
                    )
                    return False

                return True

            except (httpx.HTTPError, ValueError) as exc:

                logger.warning(
                    "Batch delivery failed (attempt %s): %s",
                    attempt + 1,
                    exc
                )

                if attempt < settings.MAX_RETRIES:
                    delay = (
                        settings.RETRY_BACKOFF * (2 ** attempt)
                    )
                    await asyncio.sleep(delay)

        logger.error("Batch delivery failed after all retries")
        return False

    async def close(self):
        await self.client.aclose()
