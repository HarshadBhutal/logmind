
from elasticsearch import AsyncElasticsearch

from logger import get_logger

logger = get_logger(__name__)

LOG_INDEX_NAME = "logmind-logs"


LOG_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "timestamp": {
                "type": "date"
            },
            "level": {
                "type": "keyword"
            },
            "message": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 1024
                    }
                }
            },
            "service": {
                "type": "keyword"
            },
            "environment": {
                "type": "keyword"
            },
            "source": {
                "type": "keyword"
            },
            "request_id": {
                "type": "keyword"
            },
            "trace_id": {
                "type": "keyword"
            },
            "span_id": {
                "type": "keyword"
            },
            "host": {
                "type": "keyword"
            },
            "attributes": {
                "type": "flattened"
            }
        }
    }
}


async def create_log_index(es: AsyncElasticsearch) -> None:
    """
    Create the LogMind index if it does not already exist.
    """

    exists = await es.indices.exists(index=LOG_INDEX_NAME)

    if exists:
        logger.info(
            "Elasticsearch index '%s' already exists",
            LOG_INDEX_NAME
        )
        return

    await es.indices.create(
        index=LOG_INDEX_NAME,
        body=LOG_INDEX_MAPPING
    )

    logger.info(
        "Elasticsearch index '%s' created successfully",
        LOG_INDEX_NAME
    )
