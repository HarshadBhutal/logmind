from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from logger import get_logger
from es import connect_es, close_es

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting LogMind")

    await connect_es()

    yield

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