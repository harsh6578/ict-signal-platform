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
def check_consequent_encroachment(
    fvg: dict,
    candles: list,
    fvg_index: int,
    validation_mode: str = "close_based",
) -> dict:
    """
    Tracks price interaction with the Consequent Encroachment (CE) level —
    the 50% midpoint of a Fair Value Gap.

    ICT theory: the first reaction at CE is a key institutional decision point.
    A "respected" CE (price reacts and moves away without invalidating) signals
    strong continuation in the FVG's direction. A "broken" CE signals weakness
    and increases the probability of full mitigation.

    validation_mode:
        "close_based" (default) - wick may pierce CE, but the candle CLOSE must
            remain on the correct side of CE for the reaction to count as "respected".
            A close through CE marks it "broken".
        "strict" - even a wick touching/crossing CE on the wrong side immediately
            marks it "broken". No penetration tolerance at all.

    Returns a dict (copy of fvg) with:
        ce_level        - the midpoint price (same as fvg['midpoint'])
        ce_status       - "not_yet_tested" | "respected" | "broken"
        ce_tested_at    - index of the candle where CE was first touched (or None)
        ce_broken_at    - index of the candle where CE was closed through (or None)
    """
    top = fvg["top"]
    bottom = fvg["bottom"]
    midpoint = fvg["midpoint"]
    is_bullish_fvg = fvg["type"] == "bullish_fvg"

    ce_status = "not_yet_tested"
    ce_tested_at = None
    ce_broken_at = None

    for i in range(fvg_index + 1, len(candles)):
        candle = candles[i]

        if is_bullish_fvg:
            # bullish FVG: price should stay above CE. Touched when low <= midpoint.
            touched = candle.low_price <= midpoint
            if not touched:
                continue

            if ce_tested_at is None:
                ce_tested_at = i

            if validation_mode == "strict":
                ce_status = "broken"
                ce_broken_at = i
                break
            else:  # close_based
                if candle.close_price < midpoint:
                    ce_status = "broken"
                    ce_broken_at = i
                    break
                else:
                    ce_status = "respected"

        else:
            # bearish FVG: price should stay below CE. Touched when high >= midpoint.
            touched = candle.high_price >= midpoint
            if not touched:
                continue

            if ce_tested_at is None:
                ce_tested_at = i

            if validation_mode == "strict":
                ce_status = "broken"
                ce_broken_at = i
                break
            else:  # close_based
                if candle.close_price > midpoint:
                    ce_status = "broken"
                    ce_broken_at = i
                    break
                else:
                    ce_status = "respected"

        # stop scanning once the FVG itself is fully mitigated —
        # CE relevance ends once the whole gap is filled
        if is_bullish_fvg and candle.close_price < bottom:
            break
        if not is_bullish_fvg and candle.close_price > top:
            break

    result = dict(fvg)
    result["ce_level"] = midpoint
    result["ce_status"] = ce_status
    result["ce_tested_at"] = ce_tested_at
    result["ce_broken_at"] = ce_broken_at
    return result
def detect_balanced_price_range(fvgs: list, max_candle_distance: int = None) -> list:
    """
    Detects Balanced Price Ranges (BPR) — ICT's highest-probability FVG-based
    PD Array. A BPR forms where a bullish FVG and a bearish FVG overlap in
    price, meaning both buy-side and sell-side institutional imbalances
    exist at the same level. This is a stronger reaction zone than either
    FVG alone.

    ICT rule: overlap_top = min(fvg1.top, fvg2.top)
              overlap_bottom = max(fvg1.bottom, fvg2.bottom)
              valid only if overlap_top > overlap_bottom
    The BPR's own CE (Consequent Encroachment) is the midpoint of the
    overlap zone itself — NOT either source FVG's individual midpoint.

    fvgs: list of FVG dicts from detect_fair_value_gaps().
    max_candle_distance: optional engineering filter (not an ICT rule) —
        if set, only pairs whose candle_3 indices are within this many
        candles of each other are considered. None = no limit (matches
        the literal ICT definition).

    Returns a list of dicts:
        {
            "type": "bullish_bpr" or "bearish_bpr",
            "top": ..., "bottom": ..., "midpoint": ...,   # overlap zone + its CE
            "source_fvg_1": <fvg dict>,
            "source_fvg_2": <fvg dict>,
        }

    Note: BPR type follows the direction of formation - a bullish BPR forms
    when a bearish FVG is later overlapped by a bullish FVG (buy-side
    resolution), and vice versa. We label it by which FVG formed second,
    since that's the FVG whose direction price is currently resolving in.
    """
    bprs = []

    for i in range(len(fvgs)):
        for j in range(i + 1, len(fvgs)):
            fvg_a = fvgs[i]
            fvg_b = fvgs[j]

            # must be opposite types to form a BPR
            if fvg_a["type"] == fvg_b["type"]:
                continue

            if max_candle_distance is not None:
                index_a = fvg_a["candle_3"].id if hasattr(fvg_a["candle_3"], "id") else None
                index_b = fvg_b["candle_3"].id if hasattr(fvg_b["candle_3"], "id") else None
                if index_a is not None and index_b is not None:
                    if abs(index_a - index_b) > max_candle_distance:
                        continue

            overlap_top = min(fvg_a["top"], fvg_b["top"])
            overlap_bottom = max(fvg_a["bottom"], fvg_b["bottom"])

            if overlap_top <= overlap_bottom:
                continue  # no actual overlap

            # whichever FVG formed later determines the BPR's directional label
            later_fvg = fvg_b if j > i else fvg_a
            bpr_type = "bullish_bpr" if later_fvg["type"] == "bullish_fvg" else "bearish_bpr"

            bprs.append({
                "type": bpr_type,
                "top": overlap_top,
                "bottom": overlap_bottom,
                "midpoint": (overlap_top + overlap_bottom) / 2,
                "source_fvg_1": fvg_a,
                "source_fvg_2": fvg_b,
            })

    return bprs
def detect_stacked_fvgs(fvgs: list) -> list:
    """
    Detects FVG stacking — multiple same-direction Fair Value Gaps forming
    consecutively within a single directional price expansion. ICT reads
    this as a sign of extreme institutional urgency: the market is unlikely
    to offer a deep retracement before reaching its target, so ICT traders
    favor entries at the CE of the MOST RECENT gap in the stack rather than
    waiting for a return to the earliest one.

    fvgs: list of FVG dicts from detect_fair_value_gaps(), in chronological
        order (oldest to newest — same order the detector produces).

    A stack is a run of 2+ consecutive same-type FVGs in the list with no
    opposite-type FVG breaking the sequence. "Consecutive" here means
    adjacent in the fvgs list (i.e., no opposite-direction FVG occurred
    between them) — it does NOT require candles to be back-to-back, since
    a directional expansion often has non-FVG candles between each gap.

    Returns a list of dicts:
        {
            "type": "bullish_stack" or "bearish_stack",
            "fvgs": [<fvg1>, <fvg2>, ...],   # the gaps in the stack, in order
            "entry_fvg": <fvg dict>,         # most recent gap - CE is the entry per ICT
            "top": ..., "bottom": ...,       # full span of the stack
        }
    """
    stacks = []
    current_run = []

    def flush_run():
        if len(current_run) >= 2:
            fvg_type = current_run[0]["type"]
            stack_label = "bullish_stack" if fvg_type == "bullish_fvg" else "bearish_stack"
            all_tops = [f["top"] for f in current_run]
            all_bottoms = [f["bottom"] for f in current_run]
            stacks.append({
                "type": stack_label,
                "fvgs": list(current_run),
                "entry_fvg": current_run[-1],
                "top": max(all_tops),
                "bottom": min(all_bottoms),
            })

    for fvg in fvgs:
        if current_run and fvg["type"] != current_run[-1]["type"]:
            flush_run()
            current_run = [fvg]
        else:
            current_run.append(fvg)

    flush_run()  # catch the final run after the loop ends

    return stacks
def detect_nested_fvgs(htf_fvgs: list, ltf_fvgs: list) -> list:
    """
    Detects Nested FVGs — a lower-timeframe FVG whose price range forms
    entirely inside a higher-timeframe FVG's price range. ICT treats the
    HTF FVG as the target/context zone and the nested LTF FVG inside it
    as the precise entry trigger ("layered institutional interest").

    htf_fvgs: FVG dicts from detect_fair_value_gaps() run on HTF candles.
    ltf_fvgs: FVG dicts from detect_fair_value_gaps() run on LTF candles.
    (Caller is responsible for detecting each list on its own timeframe's
    candles — this function only compares already-detected FVGs.)

    Containment rule: ltf_fvg is nested inside htf_fvg when
        ltf_fvg.top <= htf_fvg.top AND ltf_fvg.bottom >= htf_fvg.bottom
    (the LTF gap's full range sits within the HTF gap's full range).

    same_direction is reported (not filtered out) because both aligned
    and counter-trend nestings are meaningful: same-direction nesting is
    the classic HTF-target / LTF-entry setup; opposite-direction nesting
    can flag an early reversal signal inside the HTF zone.

    Returns a list of dicts:
        {
            "htf_fvg": <fvg dict>,
            "ltf_fvg": <fvg dict>,
            "same_direction": True/False,
            "top": ltf_fvg["top"], "bottom": ltf_fvg["bottom"],
            "midpoint": ltf_fvg["midpoint"],   # the LTF FVG is the entry zone
        }
    """
    nested = []

    for htf_fvg in htf_fvgs:
        for ltf_fvg in ltf_fvgs:
            is_contained = (
                ltf_fvg["top"] <= htf_fvg["top"]
                and ltf_fvg["bottom"] >= htf_fvg["bottom"]
            )
            if not is_contained:
                continue

            nested.append({
                "htf_fvg": htf_fvg,
                "ltf_fvg": ltf_fvg,
                "same_direction": ltf_fvg["type"] == htf_fvg["type"],
                "top": ltf_fvg["top"],
                "bottom": ltf_fvg["bottom"],
                "midpoint": ltf_fvg["midpoint"],
            })

    return nested
def grade_fvg_quality(fvg: dict) -> dict:
    """
    Grades FVG formation quality based on displacement strength — ICT's
    weak / quietly strong / exceptional tiering. Not every 3-candle gap
    is a genuine institutional footprint; this checks HOW the gap formed,
    not just that it exists.

    Rule (official ICT):
        - displacement_confirmed: candle_2 closes beyond candle_1's range
            (bullish: candle_2.close > candle_1.high;
             bearish: candle_2.close < candle_1.low)
        - continuation_confirmed: candle_3 extends beyond candle_2's extreme
            (bullish: candle_3.high > candle_2.high;
             bearish: candle_3.low < candle_2.low)

        quality = "exceptional"    if both confirmed
                = "quietly_strong" if only displacement_confirmed
                = "weak"           if displacement not confirmed at all

    fvg: a single FVG dict from detect_fair_value_gaps() - must still have
        candle_1/candle_2/candle_3 references (call this before stripping
        candle objects, if you ever do so downstream).

    Returns a dict (copy of fvg) with:
        quality                 - "weak" | "quietly_strong" | "exceptional"
        displacement_confirmed  - bool
        continuation_confirmed  - bool
    """
    candle_1 = fvg["candle_1"]
    candle_2 = fvg["candle_2"]
    candle_3 = fvg["candle_3"]

    if fvg["type"] == "bullish_fvg":
        displacement_confirmed = candle_2.close_price > candle_1.high_price
        continuation_confirmed = candle_3.high_price > candle_2.high_price
    else:  # bearish_fvg
        displacement_confirmed = candle_2.close_price < candle_1.low_price
        continuation_confirmed = candle_3.low_price < candle_2.low_price

    if displacement_confirmed and continuation_confirmed:
        quality = "exceptional"
    elif displacement_confirmed:
        quality = "quietly_strong"
    else:
        quality = "weak"

    result = dict(fvg)
    result["quality"] = quality
    result["displacement_confirmed"] = displacement_confirmed
    result["continuation_confirmed"] = continuation_confirmed
    return result
def classify_fvg_premium_discount(fvg: dict, dealing_range_top: float, dealing_range_bottom: float) -> dict:
    """
    Classifies an FVG's location relative to the Premium/Discount framework.

    ICT rule: equilibrium = 50% midpoint of the dealing range (a significant
    swing low to swing high, or vice versa - supplied by the caller, typically
    from Market Structure swing detection). Above equilibrium = premium
    (expensive, sell zone). Below equilibrium = discount (cheap, buy zone).

    "Aligned" FVGs are the ones ICT actually trades: a bullish FVG sitting in
    discount (buying cheap, in the direction of an expected upmove) or a
    bearish FVG sitting in premium (selling expensive). A bullish FVG stuck
    in premium, or a bearish FVG stuck in discount, is generally ignored -
    it's fighting the framework, not using it.

    fvg: a single FVG dict from detect_fair_value_gaps().
    dealing_range_top: the swing high of the dealing range.
    dealing_range_bottom: the swing low of the dealing range.

    Returns a dict (copy of fvg) with:
        equilibrium  - the 50% midpoint of the dealing range
        zone         - "premium" | "discount" | "equilibrium"
                       (based on the FVG's own midpoint vs equilibrium)
        is_aligned   - True if the FVG's direction matches ICT's expected zone
                       (bullish -> discount, bearish -> premium)
    """
    equilibrium = (dealing_range_top + dealing_range_bottom) / 2
    fvg_midpoint = fvg["midpoint"]

    if fvg_midpoint > equilibrium:
        zone = "premium"
    elif fvg_midpoint < equilibrium:
        zone = "discount"
    else:
        zone = "equilibrium"

    is_bullish = fvg["type"] == "bullish_fvg"
    is_aligned = (is_bullish and zone == "discount") or (not is_bullish and zone == "premium")

    result = dict(fvg)
    result["equilibrium"] = equilibrium
    result["zone"] = zone
    result["is_aligned"] = is_aligned
    return result
def _same_fvg(fvg_a: dict, fvg_b: dict) -> bool:
    """Identity check for FVGs across enriched copies - matches by the
    original candle references, which stay stable through dict(fvg) copies."""
    return (
        fvg_a.get("candle_1") is fvg_b.get("candle_1")
        and fvg_a.get("candle_3") is fvg_b.get("candle_3")
    )


def score_fvg_context(fvg: dict, stacks: list = None, nested_pairs: list = None, bprs: list = None) -> dict:
    """
    Scores an FVG's contextual importance by combining every FVG-internal
    confluence built so far. NOT an official ICT numeric rule - ICT teaches
    confluence qualitatively (more overlapping concepts = higher probability).
    These point weights are an engineering interpretation for ranking/sorting
    FVGs programmatically.

    Designed to be extended later: once Order Blocks and Liquidity modules
    exist, pass their outputs in as additional optional parameters and add
    more scoring branches - existing callers won't break.

    fvg: an FVG dict that should already be enriched by grade_fvg_quality()
        and classify_fvg_premium_discount() (reads "quality" and "is_aligned"
        if present; skips those factors silently if missing).
    stacks: optional output of detect_stacked_fvgs().
    nested_pairs: optional output of detect_nested_fvgs().
    bprs: optional output of detect_balanced_price_range().

    Returns a dict (copy of fvg) with:
        confluence_score    - int, higher = more confluence
        confluence_factors  - list of strings naming which factors fired
    """
    factors = []
    score = 0

    quality = fvg.get("quality")
    if quality == "exceptional":
        score += 2
        factors.append("exceptional_displacement")
    elif quality == "quietly_strong":
        score += 1
        factors.append("quietly_strong_displacement")

    if fvg.get("is_aligned"):
        score += 1
        factors.append("aligned_with_premium_discount")

    if stacks:
        for stack in stacks:
            if any(_same_fvg(fvg, f) for f in stack["fvgs"]):
                score += 1
                factors.append("part_of_stacked_fvgs")
                break

    if nested_pairs:
        for pair in nested_pairs:
            if _same_fvg(fvg, pair["htf_fvg"]) or _same_fvg(fvg, pair["ltf_fvg"]):
                if pair["same_direction"]:
                    score += 2
                    factors.append("nested_same_direction")
                else:
                    score += 1
                    factors.append("nested_opposite_direction")
                break

    if bprs:
        for bpr in bprs:
            if _same_fvg(fvg, bpr["source_fvg_1"]) or _same_fvg(fvg, bpr["source_fvg_2"]):
                score += 2
                factors.append("part_of_balanced_price_range")
                break

    result = dict(fvg)
    result["confluence_score"] = score
    result["confluence_factors"] = factors
    return result