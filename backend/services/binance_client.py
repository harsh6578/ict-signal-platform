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