def detect_order_blocks(candles: list, fvgs: list) -> list:
    """
    Detects ICT Order Blocks (OB) — the last opposing candle before a
    displacement move. Rather than inventing an arbitrary displacement
    threshold, we use an already-formed Fair Value Gap as proof that real
    displacement occurred (ICT itself validates OBs this way: an OB is
    confirmed when the impulse leaves behind an imbalance/FVG).

    Bullish OB: the last bearish (down-close) candle immediately before an
        FVG's candle_1, when that FVG is a bullish_fvg.
    Bearish OB: the last bullish (up-close) candle immediately before an
        FVG's candle_1, when that FVG is a bearish_fvg.

    candles: full candle list, oldest to newest.
    fvgs: list of FVG dicts from detect_fair_value_gaps() (same candles).

    Zone is marked low-to-high of the OB candle (the most commonly cited
    ICT convention - full wick range, not just the body).

    Returns a list of dicts:
        {
            "type": "bullish_ob" or "bearish_ob",
            "candle": <Candle>,          # the order block candle itself
            "top": ..., "bottom": ...,   # candle's high/low
            "source_fvg": <fvg dict>,    # the FVG that confirms displacement
        }

    Note: if the candle immediately before candle_1 is NOT opposite-colored
    (e.g., candle_1 itself IS the last opposing candle), we walk backward
    from candle_1 to find the nearest opposite-color candle - this handles
    cases where multiple same-direction candles sit right before the FVG.
    """
    order_blocks = []
    candle_to_index = {id(c): i for i, c in enumerate(candles)}

    for fvg in fvgs:
        candle_1 = fvg["candle_1"]
        c1_index = candle_to_index.get(id(candle_1))
        if c1_index is None:
            continue

        is_bullish_fvg = fvg["type"] == "bullish_fvg"

        # walk backward from candle_1 to find the nearest opposite-color candle
        ob_candle = None
        for i in range(c1_index, -1, -1):
            candle = candles[i]
            is_down_close = candle.close_price < candle.open_price
            is_up_close = candle.close_price > candle.open_price

            if is_bullish_fvg and is_down_close:
                ob_candle = candle
                break
            if not is_bullish_fvg and is_up_close:
                ob_candle = candle
                break

        if ob_candle is None:
            continue  # no opposing candle found walking back to start of data

        ob_type = "bullish_ob" if is_bullish_fvg else "bearish_ob"
        order_blocks.append({
            "type": ob_type,
            "candle": ob_candle,
            "top": ob_candle.high_price,
            "bottom": ob_candle.low_price,
            "source_fvg": fvg,
        })

    return order_blocks
def check_order_block_status(ob: dict, candles: list, ob_index: int) -> dict:
    """
    Checks whether an Order Block or Breaker Block has been touched, and
    whether it has held (mitigation) or been invalidated (breaker/re-break).

    Works for all four zone types: bullish_ob, bearish_ob, bullish_breaker,
    bearish_breaker. Bullish-direction zones (bullish_ob, bullish_breaker)
    act as support - price should stay above. Bearish-direction zones
    (bearish_ob, bearish_breaker) act as resistance - price should stay below.

    ICT rule: a wick into the zone never invalidates it - only a candle
    BODY CLOSE through the zone's far boundary does. For a bullish-direction
    zone (far boundary = its low), a body close below that low invalidates
    it. For a bearish-direction zone (far boundary = its high), a body
    close above that high invalidates it.

    ob: an order block OR breaker block dict (from detect_order_blocks() or
        convert_to_breaker_block()).
    candles: full candle list, oldest to newest.
    ob_index: index (in the full candle list) to start scanning from. For a
        fresh OB, use the OB's own candle index. For a Breaker Block, use
        its birth_index (NOT the original OB's index) so stale pre-breaker
        price action doesn't cause immediate false mitigation.

    Returns a dict (copy of ob) with:
        status       - "untested" | "mitigated" | "breaker"
        tested_at    - index of the candle that first touched the zone (or None)
        breaker_at   - index of the candle whose body closed through (or None)
    """
    top = ob["top"]
    bottom = ob["bottom"]
    is_bullish_direction = ob["type"] in ("bullish_ob", "bullish_breaker")

    status = "untested"
    tested_at = None
    breaker_at = None

    for i in range(ob_index + 1, len(candles)):
        candle = candles[i]

        if is_bullish_direction:
            touched = candle.low_price <= top
            if not touched:
                continue
            if tested_at is None:
                tested_at = i
            if candle.close_price < bottom:
                status = "breaker"
                breaker_at = i
                break
            else:
                status = "mitigated"

        else:  # bearish-direction (bearish_ob or bearish_breaker)
            touched = candle.high_price >= bottom
            if not touched:
                continue
            if tested_at is None:
                tested_at = i
            if candle.close_price > top:
                status = "breaker"
                breaker_at = i
                break
            else:
                status = "mitigated"

    result = dict(ob)
    result["status"] = status
    result["tested_at"] = tested_at
    result["breaker_at"] = breaker_at
    return result

def convert_to_breaker_block(ob_with_status: dict) -> dict:
    """
    Converts an invalidated Order Block into a Breaker Block. Only call this
    on an OB dict that has already been enriched by check_order_block_status()
    and has status == "breaker" - this function doesn't check that itself,
    since the caller is expected to filter for breakers before converting.

    ICT rule: a violated OB isn't deleted, it flips polarity. A bullish OB
    that gets a body close below its low becomes a bearish Breaker Block
    (now resistance). A bearish OB that gets a body close above its high
    becomes a bullish Breaker Block (now support). The zone itself (top/
    bottom) doesn't move - only its expected reaction direction flips.

    Critically, the Breaker gets a FRESH starting index at breaker_at (the
    candle that caused the invalidation) - not the original OB's index -
    so a future check_order_block_status() call on this Breaker won't
    immediately mark it mitigated from stale pre-breaker price action.

    ob_with_status: an OB dict already enriched by check_order_block_status(),
        expected to have status == "breaker".

    Returns a dict:
        {
            "type": "bullish_breaker" or "bearish_breaker",
            "top": ..., "bottom": ...,           # same zone as the origin OB
            "origin_ob": <the original ob_with_status dict>,
            "birth_index": ...,                   # = origin breaker_at, use this as
                                                    # ob_index for future status checks
        }
    """
    is_origin_bullish = ob_with_status["type"] == "bullish_ob"
    breaker_type = "bearish_breaker" if is_origin_bullish else "bullish_breaker"

    return {
        "type": breaker_type,
        "top": ob_with_status["top"],
        "bottom": ob_with_status["bottom"],
        "origin_ob": ob_with_status,
        "birth_index": ob_with_status["breaker_at"],
    }