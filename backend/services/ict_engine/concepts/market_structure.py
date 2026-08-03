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
def detect_internal_structure(candles: list, external_swings: list, internal_lookback: int = 1):
    """
    Detects internal (lower-timeframe-style) structure that forms
    BETWEEN each pair of consecutive external swings.

    External structure = the major, significant swings (already
    detected via find_swing_highs_and_lows + filter_significant_swings).

    Internal structure = smaller swings that form within a single
    "leg" between two consecutive external swings, used for
    entry timing and retracement analysis, independent of the
    external trend.

    candles: full list of Candle model instances, oldest to newest.
    external_swings: the cleaned/filtered external swing list.
    internal_lookback: lookback used for internal swing detection
                        (kept small since each leg is a short window).

    Returns a list of dicts like:
        {
            "leg_start": <external swing dict>,
            "leg_end": <external swing dict>,
            "leg_direction": "bullish" or "bearish",
            "internal_swings": [ ...internal swing dicts... ],
        }
    """
    legs = []

    for i in range(len(external_swings) - 1):
        leg_start = external_swings[i]
        leg_end = external_swings[i + 1]

        leg_direction = "bullish" if leg_end["price"] > leg_start["price"] else "bearish"

        start_index = leg_start["index"]
        end_index = leg_end["index"]

        # The candles strictly between the two external swings
        leg_candles = candles[start_index:end_index + 1]

        if len(leg_candles) < (internal_lookback * 2) + 3:
            # Not enough candles in this leg to meaningfully detect internal structure
            internal_swings = []
        else:
            internal_swings = find_swing_highs_and_lows(leg_candles, lookback=internal_lookback)
            # Re-map indexes back to the original full candle list, not the leg slice
            for swing in internal_swings:
                swing["index"] = swing["index"] + start_index

        legs.append({
            "leg_start": leg_start,
            "leg_end": leg_end,
            "leg_direction": leg_direction,
            "internal_swings": internal_swings,
        })

    return legs
def detect_internal_bos_and_choch(candles: list, legs: list):
    """
    Runs BOS/CHOCH detection on the internal swings within each
    external structure leg, producing "Internal BOS" / "Internal CHOCH"
    events — structure shifts on a smaller scale than the main
    external trend, used for entry timing.

    candles: full candle list, oldest to newest.
    legs: output of detect_internal_structure().

    Returns the same legs list, with each leg dict updated to include
    a new "internal_events" key containing BOS/CHOCH events scoped to
    that leg's internal swings only.
    """
    enriched_legs = []

    for leg in legs:
        internal_swings = leg["internal_swings"]

        if len(internal_swings) < 2:
            internal_events = []
        else:
            internal_events = detect_bos_and_choch(candles, internal_swings)
            for event in internal_events:
                event["type"] = "INTERNAL_" + event["type"]

        leg_copy = dict(leg)
        leg_copy["internal_events"] = internal_events
        enriched_legs.append(leg_copy)

    return enriched_legs
def detect_mss(candles: list, events: list, displacement_multiplier: float = 1.5):
    """
    Identifies which CHOCH events qualify as a true MSS (Market
    Structure Shift) — a CHOCH confirmed by a displacement candle
    (unusually large body relative to the recent average), which
    ICT considers a much more reliable reversal signal than a plain
    CHOCH alone.

    candles: full candle list, oldest to newest.
    events: BOS/CHOCH events list (from detect_bos_and_choch).
    displacement_multiplier: how many times larger than the average
        body size a candle's body must be to count as displacement.

    Returns the same events list, with each CHOCH event updated to
    include "is_mss": True/False.
    """
    body_sizes = [abs(c.close_price - c.open_price) for c in candles]
    average_body_size = sum(body_sizes) / len(body_sizes) if body_sizes else 0

    enriched_events = []
    for event in events:
        event_copy = dict(event)

        if event["type"] == "CHOCH":
            break_candle = event["break_candle"]
            body_size = abs(break_candle.close_price - break_candle.open_price)
            event_copy["is_mss"] = body_size >= (average_body_size * displacement_multiplier)
        else:
            event_copy["is_mss"] = False

        enriched_events.append(event_copy)

    return enriched_events
def analyze_market_structure(context):
    """
    Orchestrates the full Market Structure pipeline using a
    MarketContext, and stores every intermediate + final result
    back into the context so other concept modules (Liquidity, FVG,
    Order Blocks, etc.) can reuse this work without recomputing it.

    context: a MarketContext instance, already populated with candles.

    Returns the same context, now enriched with market structure results.
    """
    candles = context.candles

    raw_swings = find_swing_highs_and_lows(candles, lookback=3)
    clean_swings = filter_significant_swings(raw_swings)

    events = detect_bos_and_choch(candles, clean_swings)
    events = detect_mss(candles, events)

    classified_swings = classify_protected_and_weak_swings(clean_swings, events)

    legs = detect_internal_structure(candles, clean_swings, internal_lookback=1)
    legs = detect_internal_bos_and_choch(candles, legs)

    context.set_result("EXTERNAL_SWINGS", classified_swings)
    context.set_result("EXTERNAL_STRUCTURE_EVENTS", events)
    context.set_result("INTERNAL_STRUCTURE_LEGS", legs)

    return context