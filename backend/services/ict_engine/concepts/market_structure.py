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
def filter_significant_swings(swings: list):
    """
    Cleans up a raw swing list so it strictly alternates between
    swing_high and swing_low. When multiple swings of the same type
    occur in a row (a common side-effect of small lookback noise),
    only the most extreme one is kept (highest high, or lowest low).

    swings: list of swing dicts from find_swing_highs_and_lows(),
            already ordered oldest to newest.

    Returns a cleaned list, still ordered oldest to newest, alternating
    swing_high / swing_low.
    """
    if not swings:
        return []

    cleaned = [swings[0]]

    for swing in swings[1:]:
        last = cleaned[-1]

        if swing["type"] == last["type"]:
            # Same type as the last kept swing — keep whichever is more extreme
            if swing["type"] == "swing_high" and swing["price"] > last["price"]:
                cleaned[-1] = swing
            elif swing["type"] == "swing_low" and swing["price"] < last["price"]:
                cleaned[-1] = swing
            # otherwise, discard this swing (the existing one is already more extreme)
        else:
            cleaned.append(swing)

    return cleaned
def classify_protected_and_weak_swings(swings: list, events: list):
    """
    Classifies each swing as either "protected" (never broken while it
    was structurally relevant) or "weak" (broken by a later BOS/CHOCH,
    meaning the market treated it as an easy target rather than a
    respected level).

    swings: cleaned/filtered swing list (from filter_significant_swings).
    events: BOS/CHOCH events list (from detect_bos_and_choch).

    Returns the same swings list, with each swing dict updated to
    include a new "strength" key: either "protected" or "weak".
    """
    broken_swing_indexes = set()

    for event in events:
        broken = event["broken_swing"]
        broken_swing_indexes.add(broken["index"])

    classified = []
    for swing in swings:
        swing_copy = dict(swing)
        if swing["index"] in broken_swing_indexes:
            swing_copy["strength"] = "weak"
        else:
            swing_copy["strength"] = "protected"
        classified.append(swing_copy)

    return classified