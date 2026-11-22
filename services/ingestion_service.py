
from elasticsearch.helpers import async_bulk

from db.es import get_es
from db.index import LOG_INDEX_NAME
from ingestion.schemas import BatchLogRequest
from logger import get_logger

logger = get_logger(__name__)


async def ingest_logs(batch: BatchLogRequest) -> dict:
    """
    Insert a batch of log events into Elasticsearch.
    """

    es = get_es()

    actions = [
        {
            "_index": LOG_INDEX_NAME,
            "_source": event.model_dump(
                mode="json",
                exclude_none=True
            )
        }
        for event in batch.events
    ]

    success_count, errors = await async_bulk(
        es,
        actions,
        raise_on_error=False,
        raise_on_exception=True
    )

    failed_count = len(errors)

    # Keep the response manageable if many documents fail.
    error_details = []

    for item in errors[:20]:
        operation, details = next(iter(item.items()))

        error = details.get("error", {})

        error_details.append({
            "operation": operation,
            "id": details.get("_id"),
            "type": error.get("type") if isinstance(error, dict) else None,
            "reason": error.get("reason") if isinstance(error, dict) else str(error)
        })

    logger.info(
        "Log ingestion completed: accepted=%s failed=%s",
        success_count,
        failed_count
    )

    if failed_count:
        logger.warning(
            "%s log events failed during Elasticsearch insertion",
            failed_count
        )

    return {
        "accepted": success_count,
        "failed": failed_count,
        "errors": error_details
    }
