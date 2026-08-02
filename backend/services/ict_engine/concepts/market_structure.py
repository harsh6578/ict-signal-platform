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