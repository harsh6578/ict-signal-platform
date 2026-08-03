def detect_equal_highs_and_lows(swings: list, tolerance_percent: float = 0.1):
    """
    Detects Equal Highs (EQH) and Equal Lows (EQL) — pairs (or groups)
    of swing highs/lows that sit within a small tolerance of each
    other, which ICT considers strong liquidity pools since obvious
    "double top/bottom"-looking levels attract stop-loss and
    breakout orders.

    swings: cleaned/filtered swing list (with "type" and "price" keys),
            typically from context.get_results("EXTERNAL_SWINGS").
    tolerance_percent: how close two swing prices must be (as a
        percentage of price) to be considered "equal". Real markets
        rarely produce exact matches, so a small tolerance is used
        (this covers what ICT calls "Relative Equal Highs/Lows" too).

    Returns a list of dicts like:
        {
            "type": "equal_highs" or "equal_lows",
            "swings": [swing_a, swing_b, ...],
            "average_price": 63500.25,
        }
    """
    highs = [s for s in swings if s["type"] == "swing_high"]
    lows = [s for s in swings if s["type"] == "swing_low"]

    equal_groups = []

    for swing_list, label in [(highs, "equal_highs"), (lows, "equal_lows")]:
        used_indexes = set()

        for i in range(len(swing_list)):
            if swing_list[i]["index"] in used_indexes:
                continue

            group = [swing_list[i]]

            for j in range(i + 1, len(swing_list)):
                if swing_list[j]["index"] in used_indexes:
                    continue

                price_diff_percent = abs(swing_list[i]["price"] - swing_list[j]["price"]) / swing_list[i]["price"] * 100

                if price_diff_percent <= tolerance_percent:
                    group.append(swing_list[j])
                    used_indexes.add(swing_list[j]["index"])

            if len(group) >= 2:
                used_indexes.add(swing_list[i]["index"])
                average_price = sum(s["price"] for s in group) / len(group)
                equal_groups.append({
                    "type": label,
                    "swings": group,
                    "average_price": average_price,
                })

    return equal_groups
def detect_liquidity_sweeps(candles: list, swings: list):
    """
    Detects liquidity sweeps/grabs: moments where price briefly
    trades beyond a swing high (Buy Side Liquidity) or swing low
    (Sell Side Liquidity) and then closes back on the other side —
    the classic ICT sign of institutional stop-hunting/liquidity
    collection before a real move in the opposite direction.

    candles: full candle list, oldest to newest.
    swings: cleaned/filtered swing list.

    Returns a list of dicts like:
        {
            "liquidity_type": "buy_side" or "sell_side",
            "swept_swing": <swing dict>,
            "sweep_candle": <Candle>,
            "wick_price": 65200.0,
            "close_price": 64950.0,
        }
    """
    sweeps = []

    for swing in swings:
        swing_index = swing["index"]

        for i in range(swing_index + 1, len(candles)):
            candle = candles[i]

            if swing["type"] == "swing_high":
                wick_beyond = candle.high_price > swing["price"]
                closed_back_below = candle.close_price < swing["price"]

                if wick_beyond and closed_back_below:
                    sweeps.append({
                        "liquidity_type": "buy_side",
                        "swept_swing": swing,
                        "sweep_candle": candle,
                        "wick_price": candle.high_price,
                        "close_price": candle.close_price,
                    })
                    break
                elif candle.close_price > swing["price"]:
                    # Price broke and stayed above — this is a real BOS/CHOCH, not a sweep
                    break

            else:  # swing_low
                wick_beyond = candle.low_price < swing["price"]
                closed_back_above = candle.close_price > swing["price"]

                if wick_beyond and closed_back_above:
                    sweeps.append({
                        "liquidity_type": "sell_side",
                        "swept_swing": swing,
                        "sweep_candle": candle,
                        "wick_price": candle.low_price,
                        "close_price": candle.close_price,
                    })
                    break
                elif candle.close_price < swing["price"]:
                    break

    return sweeps
def detect_resting_liquidity(swings: list, equal_groups: list, sweeps: list):
    """
    Identifies liquidity that has NOT yet been swept — i.e. still
    "resting" and available as a future target for price (ICT's
    "Draw On Liquidity" concept). Cross-references all known liquidity
    (individual significant swings + equal highs/lows groups) against
    the sweeps already detected.
    """
    swept_swing_indexes = {s["swept_swing"]["index"] for s in sweeps}

    resting_individual = [
        s for s in swings if s["index"] not in swept_swing_indexes
    ]

    resting_groups = [
        g for g in equal_groups
        if not any(s["index"] in swept_swing_indexes for s in g["swings"])
    ]

    return {
        "resting_individual_swings": resting_individual,
        "resting_equal_groups": resting_groups,
    }
def mark_bsl_ssl_zones(swings: list):
    """
    Explicitly labels each swing as a Buy Side Liquidity (BSL) zone
    (swing highs) or Sell Side Liquidity (SSL) zone (swing lows).
    """
    zones = []
    for swing in swings:
        zone_type = "BSL" if swing["type"] == "swing_high" else "SSL"
        zones.append({**swing, "liquidity_zone_type": zone_type})
    return zones


def analyze_liquidity(context):
    """
    Orchestrates the full Liquidity pipeline using a MarketContext
    that has already had analyze_market_structure() run on it
    (since liquidity detection depends on external swings).
    """
    candles = context.candles
    swings = context.get_results("EXTERNAL_SWINGS")

    zones = mark_bsl_ssl_zones(swings)
    equal_groups = detect_equal_highs_and_lows(swings)
    sweeps = detect_liquidity_sweeps(candles, swings)
    resting = detect_resting_liquidity(swings, equal_groups, sweeps)

    context.set_result("LIQUIDITY_ZONES", zones)
    context.set_result("EQUAL_HIGHS_LOWS", equal_groups)
    context.set_result("LIQUIDITY_SWEEPS", sweeps)
    context.set_result("RESTING_LIQUIDITY", resting)

    return context
def detect_inducement(sweeps: list, resting: list):
    """
    Flags a sweep as "inducement" if a larger resting liquidity pool
    exists further beyond it in the same direction — meaning this
    sweep likely lured traders before price targets the bigger pool.
    """
    resting_swings = resting["resting_individual_swings"]
    inducements = []

    for sweep in sweeps:
        swept = sweep["swept_swing"]
        same_type_resting = [
            s for s in resting_swings if s["type"] == swept["type"]
        ]

        for candidate in same_type_resting:
            if swept["type"] == "swing_high" and candidate["price"] > swept["price"]:
                inducements.append({"induced_swing": swept, "real_target": candidate, "sweep": sweep})
                break
            elif swept["type"] == "swing_low" and candidate["price"] < swept["price"]:
                inducements.append({"induced_swing": swept, "real_target": candidate, "sweep": sweep})
                break

    return inducements


def detect_trendline_liquidity(swings: list, min_points: int = 3):
    """
    Detects diagonal trendline liquidity: 3+ consecutive swing highs
    forming a descending line, or 3+ consecutive swing lows forming
    an ascending line.
    """
    highs = [s for s in swings if s["type"] == "swing_high"]
    lows = [s for s in swings if s["type"] == "swing_low"]

    trendlines = []

    for i in range(len(highs) - min_points + 1):
        window = highs[i:i + min_points]
        if all(window[j]["price"] > window[j + 1]["price"] for j in range(len(window) - 1)):
            trendlines.append({"type": "descending_trendline", "points": window})

    for i in range(len(lows) - min_points + 1):
        window = lows[i:i + min_points]
        if all(window[j]["price"] < window[j + 1]["price"] for j in range(len(window) - 1)):
            trendlines.append({"type": "ascending_trendline", "points": window})

    return trendlines


def detect_old_highs_lows(swings: list, resting: list, age_threshold: int = 30):
    """
    Flags resting swings as "old" if they are older (by candle index
    distance from the most recent candle) than age_threshold candles.
    """
    if not swings:
        return []

    most_recent_index = max(s["index"] for s in swings)
    resting_indexes = {s["index"] for s in resting["resting_individual_swings"]}

    old_swings = [
        s for s in swings
        if s["index"] in resting_indexes and (most_recent_index - s["index"]) >= age_threshold
    ]
    return old_swings