from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from core.logging_config import logger

scheduler = BackgroundScheduler()


def _job_listener(event):
    if event.exception:
        logger.info(f"Scheduled job '{event.job_id}' FAILED: {event.exception}")
    else:
        logger.info(f"Scheduled job '{event.job_id}' completed successfully")


def refresh_recent_candles():
    """
    Periodically re-fetches the most recent candles from Binance as a
    safety net, in case the live WebSocket stream missed anything
    during a brief disconnect/reconnect.
    """
    from services.binance_client import get_klines, store_klines

    symbol = "BTCUSDT"
    timeframe = "1m"

    try:
        klines = get_klines(symbol, timeframe, limit=10)
        count = store_klines(symbol, timeframe, klines)
        logger.info(f"[Scheduled refresh] Checked recent candles for {symbol} {timeframe} — stored {count} new")
    except Exception as e:
        logger.info(f"[Scheduled refresh] Failed to refresh candles: {e}")


def start_scheduler():
    scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.add_job(
        refresh_recent_candles,
        "interval",
        minutes=5,
        id="refresh_recent_candles",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    scheduler.start()
    logger.info("APScheduler started")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler shut down")