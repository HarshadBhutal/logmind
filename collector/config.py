
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectorSettings(BaseSettings):

    READ_FROM_START: bool = False

    SHUTDOWN_TIMEOUT: float = Field(default=30.0, gt=0)
    
    # Application information
    SERVICE_NAME: str = "logmind-demo"
    ENVIRONMENT: str = "development"

    # File reader
    LOG_FILE_PATH: Path = Path("logs/app.log")
    POLL_INTERVAL: float = Field(default=0.5, gt=0)

    # Buffer and batch processing
    BUFFER_CAPACITY: int = Field(default=1000, gt=0)
    BATCH_SIZE: int = Field(default=100, gt=0)

    # Backend communication
    INGESTION_URL: str = "http://localhost:8000/api/v1/ingest"
    REQUEST_TIMEOUT: float = Field(default=10.0, gt=0)

    # Retry configuration
    MAX_RETRIES: int = Field(default=3, ge=0)
    RETRY_BACKOFF: float = Field(default=1.0, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COLLECTOR_",
        case_sensitive=True,
        extra="ignore"
    )


settings = CollectorSettings()
