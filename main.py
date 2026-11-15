
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from config import settings
from logger import get_logger
from db.es import connect_es, close_es, get_es

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting LogMind")

    await connect_es()

    try:
        yield
    finally:
        await close_es()
        logger.info("Shutting down LogMind")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)


@app.get("/health")
async def health():

    return {
        "status": "running",
        "application": settings.APP_NAME
    }


@app.get("/ready")
async def readiness():

    try:
        es = get_es()
        await es.info()

        return {
            "status": "ready",
            "elasticsearch": "connected"
        }

    except Exception:
        logger.exception("Readiness check failed")

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "elasticsearch": "unavailable"
            }
        )
