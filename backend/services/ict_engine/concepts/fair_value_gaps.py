def detect_fair_value_gaps(candles: list):
    """
    Detects standard 3-candle Fair Value Gaps (FVG) — ICT's core
    "inefficiency" concept: a candle sequence where the middle candle's
    momentum leaves an untraded gap between candle 1 and candle 3.

    Bullish FVG: candle[i-1].high < candle[i+1].low
        (gap sits between candle[i-1].high and candle[i+1].low)
    Bearish FVG: candle[i-1].low > candle[i+1].high
        (gap sits between candle[i+1].high and candle[i-1].low)

    candles: full candle list, oldest to newest.

    Returns a list of dicts like:
        {
            "type": "bullish_fvg" or "bearish_fvg",
            "candle_1": <Candle>, "candle_2": <Candle>, "candle_3": <Candle>,
            "top": 63500.0, "bottom": 63400.0,
            "midpoint": 63450.0,   # Consequent Encroachment level
        }
    """
    fvgs = []

    for i in range(1, len(candles) - 1):
        prev_candle = candles[i - 1]
        next_candle = candles[i + 1]

        if prev_candle.high_price < next_candle.low_price:
            top = next_candle.low_price
            bottom = prev_candle.high_price
            fvgs.append({
                "type": "bullish_fvg",
                "candle_1": prev_candle,
                "candle_2": candles[i],
                "candle_3": next_candle,
                "top": top,
                "bottom": bottom,
                "midpoint": (top + bottom) / 2,
            })

        elif prev_candle.low_price > next_candle.high_price:
            top = prev_candle.low_price
            bottom = next_candle.high_price
            fvgs.append({
                "type": "bearish_fvg",
                "candle_1": prev_candle,
                "candle_2": candles[i],
                "candle_3": next_candle,
                "top": top,
                "bottom": bottom,
                "midpoint": (top + bottom) / 2,
            })

    return fvgs
def check_fvg_mitigation(fvg: dict, candles: list, fvg_index: int):
    """
    Checks how much of an FVG has been mitigated (traded back into)
    by candles after it formed, and whether it has flipped into an
    IFVG (Inversed FVG) — fully mitigated AND price closed through
    to the opposite side, meaning the zone now acts as the opposite
    polarity (a bullish FVG that gets fully violated becomes a
    bearish IFVG, and vice versa).

    fvg: a single FVG dict from detect_fair_value_gaps().
    candles: full candle list, oldest to newest.
    fvg_index: the index (in the full candle list) of the FVG's
        candle_3 (the candle right after formation), so we only
        check candles that come after the FVG existed.
    """
    top = fvg["top"]
    bottom = fvg["bottom"]
    midpoint = fvg["midpoint"]

    mitigation_status = "unmitigated"
    is_ifvg = False

    for candle in candles[fvg_index + 1:]:
        if fvg["type"] == "bullish_fvg":
            if candle.low_price <= midpoint:
                mitigation_status = "partially_mitigated"
            if candle.low_price <= bottom:
                mitigation_status = "fully_mitigated"
            if candle.close_price < bottom:
                is_ifvg = True
                break
        else:  # bearish_fvg
            if candle.high_price >= midpoint:
                mitigation_status = "partially_mitigated"
            if candle.high_price >= top:
                mitigation_status = "fully_mitigated"
            if candle.close_price > top:
                is_ifvg = True
                break

    result = dict(fvg)
    result["mitigation_status"] = mitigation_status
    result["is_ifvg"] = is_ifvg
    return result