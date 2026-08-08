"""
Test script for check_consequent_encroachment().
Run from the backend/ directory: python3 test_consequent_encroachment.py

Uses lightweight synthetic candle objects (only the attributes the function
actually reads: low_price, high_price, close_price) so tests are fully
deterministic and don't depend on the database.
"""

from services.ict_engine.concepts.fair_value_gaps import check_consequent_encroachment


class MockCandle:
    """Minimal stand-in for the Candle model - only the fields CE logic needs."""
    def __init__(self, low_price, high_price, close_price):
        self.low_price = low_price
        self.high_price = high_price
        self.close_price = close_price


def make_bullish_fvg(top=110, bottom=100):
    midpoint = (top + bottom) / 2
    return {
        "type": "bullish_fvg",
        "top": top,
        "bottom": bottom,
        "midpoint": midpoint,
    }


def make_bearish_fvg(top=110, bottom=100):
    midpoint = (top + bottom) / 2
    return {
        "type": "bearish_fvg",
        "top": top,
        "bottom": bottom,
        "midpoint": midpoint,
    }


def run_test(name, actual, expected_status, expected_tested=None, expected_broken=None):
    passed = actual["ce_status"] == expected_status
    if expected_tested is not None:
        passed = passed and actual["ce_tested_at"] == expected_tested
    if expected_broken is not None:
        passed = passed and actual["ce_broken_at"] == expected_broken

    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    ce_status={actual['ce_status']}  ce_tested_at={actual['ce_tested_at']}  ce_broken_at={actual['ce_broken_at']}")
    if not passed:
        print(f"    expected: ce_status={expected_status}  ce_tested_at={expected_tested}  ce_broken_at={expected_broken}")
    return passed


results = []

# --- Test 1: Bullish FVG, CE respected (close-based, wick pierces but close holds) ---
fvg = make_bullish_fvg(top=110, bottom=100)  # midpoint = 105
candles = [
    MockCandle(low_price=115, high_price=120, close_price=118),  # not near CE
    MockCandle(low_price=104, high_price=112, close_price=106),  # wick pierces CE, close holds above
]
result = check_consequent_encroachment(fvg, candles, fvg_index=-1, validation_mode="close_based")
results.append(run_test("Bullish FVG - CE respected (close_based)", result, "respected", expected_tested=1))

# --- Test 2: Bullish FVG, CE broken (close-based, close goes below midpoint) ---
fvg = make_bullish_fvg(top=110, bottom=100)  # midpoint = 105
candles = [
    MockCandle(low_price=115, high_price=120, close_price=118),
    MockCandle(low_price=103, high_price=108, close_price=103),  # closes below CE
]
result = check_consequent_encroachment(fvg, candles, fvg_index=-1, validation_mode="close_based")
results.append(run_test("Bullish FVG - CE broken (close_based)", result, "broken", expected_tested=1, expected_broken=1))

# --- Test 3: Strict mode - same wick-only touch as Test 1, but should break in strict mode ---
fvg = make_bullish_fvg(top=110, bottom=100)  # midpoint = 105
candles = [
    MockCandle(low_price=115, high_price=120, close_price=118),
    MockCandle(low_price=104, high_price=112, close_price=106),  # wick pierces CE
]
result = check_consequent_encroachment(fvg, candles, fvg_index=-1, validation_mode="strict")
results.append(run_test("Bullish FVG - CE broken (strict mode)", result, "broken", expected_tested=1, expected_broken=1))

# --- Test 4: CE not yet tested - price never reaches midpoint ---
fvg = make_bullish_fvg(top=110, bottom=100)  # midpoint = 105
candles = [
    MockCandle(low_price=115, high_price=120, close_price=118),
    MockCandle(low_price=112, high_price=116, close_price=114),
]
result = check_consequent_encroachment(fvg, candles, fvg_index=-1, validation_mode="close_based")
results.append(run_test("Bullish FVG - CE not yet tested", result, "not_yet_tested", expected_tested=None))

# --- Test 5: Bearish FVG - CE respected (mirror of Test 1) ---
fvg = make_bearish_fvg(top=110, bottom=100)  # midpoint = 105
candles = [
    MockCandle(low_price=90, high_price=95, close_price=92),   # not near CE
    MockCandle(low_price=98, high_price=106, close_price=104), # wick pierces CE, close holds below
]
result = check_consequent_encroachment(fvg, candles, fvg_index=-1, validation_mode="close_based")
results.append(run_test("Bearish FVG - CE respected (close_based)", result, "respected", expected_tested=1))

# --- Test 6: Bearish FVG - CE broken (close-based) ---
fvg = make_bearish_fvg(top=110, bottom=100)  # midpoint = 105
candles = [
    MockCandle(low_price=90, high_price=95, close_price=92),
    MockCandle(low_price=104, high_price=108, close_price=107),  # closes above CE
]
result = check_consequent_encroachment(fvg, candles, fvg_index=-1, validation_mode="close_based")
results.append(run_test("Bearish FVG - CE broken (close_based)", result, "broken", expected_tested=1, expected_broken=1))

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")