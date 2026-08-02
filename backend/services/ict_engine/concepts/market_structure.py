def find_swing_highs_and_lows(candles: list, lookback: int = 1):
    """
    Detects basic swing highs and swing lows in a list of candles.

    A swing high is a candle whose high price is greater than the
    highs of `lookback` candles before AND after it.

    A swing low is a candle whose low price is lower than the lows
    of `lookback` candles before AND after it.

    candles: list of Candle model instances, ordered oldest to newest.
    lookback: how many candles on each side to compare against (default 1).

    Returns a list of dicts like:
        {"type": "swing_high", "index": 5, "candle": <Candle>, "price": 30500.0}
        {"type": "swing_low", "index": 8, "candle": <Candle>, "price": 29800.0}
    """
    swings = []

    for i in range(lookback, len(candles) - lookback):
        current = candles[i]

        left_candles = candles[i - lookback:i]
        right_candles = candles[i + 1:i + 1 + lookback]

        is_swing_high = all(current.high_price > c.high_price for c in left_candles) and \
                         all(current.high_price > c.high_price for c in right_candles)

        is_swing_low = all(current.low_price < c.low_price for c in left_candles) and \
                        all(current.low_price < c.low_price for c in right_candles)

        if is_swing_high:
            swings.append({
                "type": "swing_high",
                "index": i,
                "candle": current,
                "price": current.high_price,
            })

        if is_swing_low:
            swings.append({
                "type": "swing_low",
                "index": i,
                "candle": current,
                "price": current.low_price,
            })

    return swings
def detect_bos_and_choch(candles: list, swings: list):
    """
    Detects Break of Structure (BOS) and Change of Character (CHOCH) events.

    BOS = price breaks a swing point in the direction of the current trend
          (trend continuation).
    CHOCH = price breaks a swing point against the current trend
            (possible reversal).

    candles: list of Candle model instances, oldest to newest.
    swings: list of swing dicts from find_swing_highs_and_lows(), oldest to newest.

    Returns a list of dicts like:
        {"type": "BOS", "direction": "bullish", "broken_swing": <swing dict>, "break_candle": <Candle>, "price": 63200.0}
        {"type": "CHOCH", "direction": "bearish", "broken_swing": <swing dict>, "break_candle": <Candle>, "price": 62700.0}
    """
    events = []

    if len(swings) < 2:
        return events

    trend = None  # becomes "bullish" or "bearish" once we can tell

    last_swing_high = None
    last_swing_low = None

    for swing in swings:
        if swing["type"] == "swing_high":
            if last_swing_high is not None and trend is None:
                trend = "bullish" if swing["price"] > last_swing_high["price"] else "bearish"
            last_swing_high = swing
        else:
            if last_swing_low is not None and trend is None:
                trend = "bearish" if swing["price"] < last_swing_low["price"] else "bullish"
            last_swing_low = swing

    pending_high = None
    pending_low = None
    swing_index_map = {s["index"]: s for s in swings}

    for i, candle in enumerate(candles):
        if i in swing_index_map:
            swing = swing_index_map[i]
            if swing["type"] == "swing_high":
                pending_high = swing
            else:
                pending_low = swing
            continue

        if pending_high is not None and candle.close_price > pending_high["price"]:
            event_type = "BOS" if trend in ("bullish", None) else "CHOCH"
            events.append({
                "type": event_type,
                "direction": "bullish",
                "broken_swing": pending_high,
                "break_candle": candle,
                "price": candle.close_price,
            })
            trend = "bullish"
            pending_high = None

        if pending_low is not None and candle.close_price < pending_low["price"]:
            event_type = "BOS" if trend in ("bearish", None) else "CHOCH"
            events.append({
                "type": event_type,
                "direction": "bearish",
                "broken_swing": pending_low,
                "break_candle": candle,
                "price": candle.close_price,
            })
            trend = "bearish"
            pending_low = None

    return events