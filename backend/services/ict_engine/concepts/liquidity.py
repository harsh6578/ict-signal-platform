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