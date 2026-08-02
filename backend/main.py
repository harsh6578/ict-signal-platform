from fastapi import FastAPI

from core.config import settings
from core.logging_config import setup_logging, logger
from core.scheduler import start_scheduler, shutdown_scheduler
from services.binance_websocket import start_kline_stream

setup_logging()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.app_name} in '{settings.environment}' mode")

    start_scheduler()

    # Automatically start live data streaming when the server starts
    start_kline_stream("BTCUSDT", "1m")


@app.on_event("shutdown")
def on_shutdown():
    shutdown_scheduler()


@app.get("/health")
def health_check():
    logger.info("Health check requested")
    return {
        "status": "ok",
        "service": "ict-signal-platform-backend",
        "environment": settings.environment,
    }