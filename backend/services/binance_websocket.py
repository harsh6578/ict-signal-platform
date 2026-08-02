import json
import threading
import time

import websocket

from core.logging_config import logger
from services.binance_client import store_klines

BINANCE_WS_BASE_URL = "wss://stream.binance.com:9443/ws"

RECONNECT_DELAY_SECONDS = 5


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
    logger.info(f"WebSocket connection closed (code={close_status_code}, msg={close_msg})")


def _on_open(ws):
    logger.info("WebSocket connection opened")


def _run_stream_with_reconnect(symbol_code: str, timeframe_code: str):
    """
    Keeps the WebSocket connection alive forever.
    If it ever drops (network issue, Binance restart, etc.), waits a few
    seconds and reconnects automatically, instead of giving up silently.
    """
    stream_name = f"{symbol_code.lower()}@kline_{timeframe_code}"
    url = f"{BINANCE_WS_BASE_URL}/{stream_name}"

    while True:
        try:
            ws = websocket.WebSocketApp(
                url,
                on_open=_on_open,
                on_message=_on_message,
                on_error=_on_error,
                on_close=_on_close,
            )
            ws.run_forever()
        except Exception as e:
            logger.info(f"Unexpected error in WebSocket stream: {e}")

        logger.info(
            f"Stream for {symbol_code} {timeframe_code} disconnected. "
            f"Reconnecting in {RECONNECT_DELAY_SECONDS} seconds..."
        )
        time.sleep(RECONNECT_DELAY_SECONDS)


def start_kline_stream(symbol_code: str, timeframe_code: str):
    """
    Opens a live WebSocket connection to Binance for one symbol + timeframe.
    Runs forever in the background, automatically reconnecting if the
    connection ever drops, storing each closed candle as it happens.
    """
    thread = threading.Thread(
        target=_run_stream_with_reconnect,
        args=(symbol_code, timeframe_code),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started live kline stream for {symbol_code} {timeframe_code} (with auto-reconnect)")
    return thread 