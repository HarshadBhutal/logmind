from elasticsearch import AsyncElasticsearch

from config import settings
from logger import get_logger

logger = get_logger(__name__)

es_client: AsyncElasticsearch | None = None


async def connect_es():

    global es_client

    es_client = AsyncElasticsearch(
        hosts=[settings.ES_HOST],
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )

    try:
        info = await es_client.info()
        logger.info(
            "Connected to Elasticsearch: %s",
            info["version"]["number"]
        )

    except Exception:
        await es_client.close()
        es_client = None
        logger.exception("Elasticsearch connection failed")
        raise


async def close_es():

    global es_client

    if es_client is not None:
        await es_client.close()
        es_client = None
        logger.info("Elasticsearch connection closed")


def get_es() -> AsyncElasticsearch:

    if es_client is None:
        raise RuntimeError("Elasticsearch is not initialized")

    return es_client