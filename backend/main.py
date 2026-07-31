from fastapi import FastAPI

from core.config import settings
from core.logging_config import setup_logging, logger

setup_logging()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.app_name} in '{settings.environment}' mode")


@app.get("/health")
def health_check():
    logger.info("Health check requested")
    return {
        "status": "ok",
        "service": "ict-signal-platform-backend",
        "environment": settings.environment,
    }
