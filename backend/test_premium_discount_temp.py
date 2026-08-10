"""
Temporary test script for classify_fvg_premium_discount().
Run from backend/: python3 test_premium_discount_temp.py
Delete after validation - not a permanent regression test.
"""

from services.ict_engine.concepts.fair_value_gaps import classify_fvg_premium_discount


def make_fvg(fvg_type, top, bottom):
    return {"type": fvg_type, "top": top, "bottom": bottom, "midpoint": (top + bottom) / 2}


def run_test(name, actual, expected_zone, expected_aligned):
    passed = actual["zone"] == expected_zone and actual["is_aligned"] == expected_aligned
    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    equilibrium={actual['equilibrium']}  zone={actual['zone']}  is_aligned={actual['is_aligned']}")
    if not passed:
        print(f"    expected zone={expected_zone}  is_aligned={expected_aligned}")
    return passed


results = []
# dealing range: 100 to 200, equilibrium = 150

# --- Test 1: bullish FVG in discount -> aligned True ---
fvg = make_fvg("bullish_fvg", top=130, bottom=120)  # midpoint = 125, below EQ 150
result = classify_fvg_premium_discount(fvg, dealing_range_top=200, dealing_range_bottom=100)
results.append(run_test("Bullish FVG in discount -> aligned", result, "discount", True))

# --- Test 2: bullish FVG in premium -> aligned False ---
fvg = make_fvg("bullish_fvg", top=180, bottom=170)  # midpoint = 175, above EQ 150
result = classify_fvg_premium_discount(fvg, dealing_range_top=200, dealing_range_bottom=100)
results.append(run_test("Bullish FVG in premium -> not aligned", result, "premium", False))

# --- Test 3: bearish FVG in premium -> aligned True ---
fvg = make_fvg("bearish_fvg", top=180, bottom=170)  # midpoint = 175, above EQ 150
result = classify_fvg_premium_discount(fvg, dealing_range_top=200, dealing_range_bottom=100)
results.append(run_test("Bearish FVG in premium -> aligned", result, "premium", True))

# --- Test 4: bearish FVG in discount -> aligned False ---
fvg = make_fvg("bearish_fvg", top=130, bottom=120)  # midpoint = 125, below EQ 150
result = classify_fvg_premium_discount(fvg, dealing_range_top=200, dealing_range_bottom=100)
results.append(run_test("Bearish FVG in discount -> not aligned", result, "discount", False))

# --- Test 5: FVG exactly at equilibrium -> zone equilibrium, not aligned ---
fvg = make_fvg("bullish_fvg", top=155, bottom=145)  # midpoint = 150, exactly EQ
result = classify_fvg_premium_discount(fvg, dealing_range_top=200, dealing_range_bottom=100)
results.append(run_test("FVG exactly at equilibrium -> not aligned", result, "equilibrium", False))

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")