"""
Temporary test script for grade_fvg_quality().
Run from backend/: python3 test_fvg_quality_temp.py
Delete after validation - not a permanent regression test.
"""

from services.ict_engine.concepts.fair_value_gaps import grade_fvg_quality


class MockCandle:
    def __init__(self, low_price, high_price, close_price):
        self.low_price = low_price
        self.high_price = high_price
        self.close_price = close_price


def make_fvg(fvg_type, candle_1, candle_2, candle_3):
    return {
        "type": fvg_type,
        "candle_1": candle_1,
        "candle_2": candle_2,
        "candle_3": candle_3,
        "top": 0, "bottom": 0, "midpoint": 0,  # not used by this function
    }


def run_test(name, actual, expected_quality):
    passed = actual["quality"] == expected_quality
    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    quality={actual['quality']}  displacement_confirmed={actual['displacement_confirmed']}  continuation_confirmed={actual['continuation_confirmed']}")
    if not passed:
        print(f"    expected quality={expected_quality}")
    return passed


results = []

# --- Test 1: Bullish - exceptional (displacement + continuation) ---
c1 = MockCandle(low_price=98, high_price=100, close_price=99)
c2 = MockCandle(low_price=100, high_price=108, close_price=107)   # closes above c1.high (100)
c3 = MockCandle(low_price=106, high_price=112, close_price=110)   # high (112) beyond c2.high (108)
fvg = make_fvg("bullish_fvg", c1, c2, c3)
result = grade_fvg_quality(fvg)
results.append(run_test("Bullish - exceptional", result, "exceptional"))

# --- Test 2: Bullish - quietly strong (displacement, no continuation) ---
c1 = MockCandle(low_price=98, high_price=100, close_price=99)
c2 = MockCandle(low_price=100, high_price=108, close_price=107)   # closes above c1.high
c3 = MockCandle(low_price=104, high_price=106, close_price=105)   # high (106) does NOT beat c2.high (108)
fvg = make_fvg("bullish_fvg", c1, c2, c3)
result = grade_fvg_quality(fvg)
results.append(run_test("Bullish - quietly strong", result, "quietly_strong"))

# --- Test 3: Bullish - weak (no displacement) ---
c1 = MockCandle(low_price=98, high_price=100, close_price=99)
c2 = MockCandle(low_price=99, high_price=103, close_price=100)    # closes at c1.high, not beyond
c3 = MockCandle(low_price=101, high_price=105, close_price=104)
fvg = make_fvg("bullish_fvg", c1, c2, c3)
result = grade_fvg_quality(fvg)
results.append(run_test("Bullish - weak", result, "weak"))

# --- Test 4: Bearish - exceptional (mirror of Test 1) ---
c1 = MockCandle(low_price=100, high_price=102, close_price=101)
c2 = MockCandle(low_price=92, high_price=100, close_price=93)     # closes below c1.low (100)
c3 = MockCandle(low_price=88, high_price=94, close_price=90)      # low (88) beyond c2.low (92)
fvg = make_fvg("bearish_fvg", c1, c2, c3)
result = grade_fvg_quality(fvg)
results.append(run_test("Bearish - exceptional", result, "exceptional"))

# --- Test 5: Bearish - weak (no displacement) ---
c1 = MockCandle(low_price=100, high_price=102, close_price=101)
c2 = MockCandle(low_price=99, high_price=101, close_price=100)    # closes at c1.low, not beyond
c3 = MockCandle(low_price=95, high_price=99, close_price=96)
fvg = make_fvg("bearish_fvg", c1, c2, c3)
result = grade_fvg_quality(fvg)
results.append(run_test("Bearish - weak", result, "weak"))

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")