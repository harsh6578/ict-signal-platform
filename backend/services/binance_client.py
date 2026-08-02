import requests

from core.logging_config import logger

BINANCE_BASE_URL = "https://api.binance.com"


def get_klines(symbol: str, interval: str, limit: int = 500):
    """
    Fetch historical candlestick (kline) data from Binance's public REST API.

    symbol: e.g. "BTCUSDT"
    interval: e.g. "1m", "5m", "15m", "1h", "4h", "1d"
    limit: how many candles to fetch (max 1000 per Binance's rules)
    """
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }

    logger.info(f"Fetching klines: symbol={symbol}, interval={interval}, limit={limit}")

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()
from datetime import datetime, timezone

from core.database import SessionLocal
from models.symbol import Symbol
from models.timeframe import Timeframe
from models.candle import Candle


def store_klines(symbol_code: str, timeframe_code: str, klines: list):
    """
    Takes raw Binance kline data and stores it into our candles table.
    Skips any candle that's already stored (based on the unique constraint).
    """
    db = SessionLocal()
    try:
        symbol = db.query(Symbol).filter(Symbol.code == symbol_code).first()
        timeframe = db.query(Timeframe).filter(Timeframe.code == timeframe_code).first()

        if not symbol or not timeframe:
            logger.info(f"Symbol or timeframe not found in database: {symbol_code}, {timeframe_code}")
            return 0

        saved_count = 0

        for kline in klines:
            open_time_ms = kline[0]
            close_time_ms = kline[6]

            open_time = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
            close_time = datetime.fromtimestamp(close_time_ms / 1000, tz=timezone.utc)

            existing_candle = (
                db.query(Candle)
                .filter(
                    Candle.symbol_id == symbol.id,
                    Candle.timeframe_id == timeframe.id,
                    Candle.open_time == open_time,
                )
                .first()
            )

            if existing_candle:
                continue

            candle = Candle(
                symbol_id=symbol.id,
                timeframe_id=timeframe.id,
                open_time=open_time,
                close_time=close_time,
                open_price=float(kline[1]),
                high_price=float(kline[2]),
                low_price=float(kline[3]),
                close_price=float(kline[4]),
                volume=float(kline[5]),
            )
            db.add(candle)
            saved_count += 1

        db.commit()
        logger.info(f"Saved {saved_count} new candles for {symbol_code} {timeframe_code}")
        return saved_count
    finally:
        db.close()