import json
import threading

import websocket

from core.logging_config import logger
from services.binance_client import store_klines

BINANCE_WS_BASE_URL = "wss://stream.binance.com:9443/ws"


def _on_message(ws, message):
    data = json.loads(message)
    kline = data.get("k", {})

    is_candle_closed = kline.get("x", False)

    if not is_candle_closed:
        # Candle is still forming (live/incomplete) — we only store CLOSED candles for now
        return

    symbol_code = kline["s"]
    timeframe_code = kline["i"]

    formatted_kline = [
        kline["t"],  # open time
        kline["o"],  # open
        kline["h"],  # high
        kline["l"],  # low
        kline["c"],  # close
        kline["v"],  # volume
        kline["T"],  # close time
    ]

    count = store_klines(symbol_code, timeframe_code, [formatted_kline])
    logger.info(f"Live candle closed for {symbol_code} {timeframe_code} — stored {count} new candle(s)")


def _on_error(ws, error):
    logger.info(f"WebSocket error: {error}")


def _on_close(ws, close_status_code, close_msg):
    logger.info("WebSocket connection closed")


def _on_open(ws):
    logger.info("WebSocket connection opened")


def start_kline_stream(symbol_code: str, timeframe_code: str):
    """
    Opens a live WebSocket connection to Binance for one symbol + timeframe.
    Runs forever in the background, storing each closed candle as it happens.
    """
    stream_name = f"{symbol_code.lower()}@kline_{timeframe_code}"
    url = f"{BINANCE_WS_BASE_URL}/{stream_name}"

    ws = websocket.WebSocketApp(
        url,
        on_open=_on_open,
        on_message=_on_message,
        on_error=_on_error,
        on_close=_on_close,
    )

    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()

    logger.info(f"Started live kline stream for {symbol_code} {timeframe_code}")
    return ws