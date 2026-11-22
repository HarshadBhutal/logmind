
from fastapi import APIRouter, HTTPException, status
from elasticsearch.exceptions import ApiError, TransportError

from ingestion.schemas import BatchLogRequest, IngestionResponse
from services.ingestion_service import ingest_logs
from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Ingestion"]
)


@router.post(
    "/ingest",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK
)
async def ingest_log_events(batch: BatchLogRequest):

    try:
        result = await ingest_logs(batch)

        return result

    except (ApiError, TransportError):
        logger.exception("Elasticsearch ingestion failed")

        raise HTTPException(
            status_code=503,
            detail="Log ingestion service is temporarily unavailable"
        )

    except Exception:
        logger.exception("Unexpected error during log ingestion")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during log ingestion"
        )
