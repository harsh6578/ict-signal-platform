from apscheduler.schedulers.background import BackgroundScheduler

from core.logging_config import logger

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.start()
    logger.info("APScheduler started")


def shutdown_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler shut down")