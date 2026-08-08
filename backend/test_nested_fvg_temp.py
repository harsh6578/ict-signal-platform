"""
Temporary test script for detect_nested_fvgs().
Run from backend/: python3 test_nested_fvg_temp.py
Delete after validation - not a permanent regression test.
"""

from services.ict_engine.concepts.fair_value_gaps import detect_nested_fvgs


def make_fvg(fvg_type, top, bottom):
    return {"type": fvg_type, "top": top, "bottom": bottom, "midpoint": (top + bottom) / 2}


def run_test(name, actual_list, expected_count, expected_same_direction=None):
    passed = len(actual_list) == expected_count
    if passed and expected_count > 0 and expected_same_direction is not None:
        passed = passed and actual_list[0]["same_direction"] == expected_same_direction

    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    found {len(actual_list)} nested pair(s)")
    for n in actual_list:
        print(f"    htf={n['htf_fvg']['type']}  ltf={n['ltf_fvg']['type']}  same_direction={n['same_direction']}  entry_ce={n['midpoint']}")
    if not passed:
        print(f"    expected: count={expected_count}  same_direction={expected_same_direction}")
    return passed


results = []

# --- Test 1: LTF bullish FVG fully inside HTF bullish FVG -> nested, same direction ---
htf_fvgs = [make_fvg("bullish_fvg", top=120, bottom=100)]
ltf_fvgs = [make_fvg("bullish_fvg", top=112, bottom=105)]
result = detect_nested_fvgs(htf_fvgs, ltf_fvgs)
results.append(run_test("LTF inside HTF, same direction -> nested True", result, expected_count=1, expected_same_direction=True))

# --- Test 2: LTF bearish FVG inside HTF bullish FVG -> nested, opposite direction ---
htf_fvgs = [make_fvg("bullish_fvg", top=120, bottom=100)]
ltf_fvgs = [make_fvg("bearish_fvg", top=112, bottom=105)]
result = detect_nested_fvgs(htf_fvgs, ltf_fvgs)
results.append(run_test("LTF inside HTF, opposite direction -> nested False flag", result, expected_count=1, expected_same_direction=False))

# --- Test 3: LTF FVG partially outside HTF range -> not nested ---
htf_fvgs = [make_fvg("bullish_fvg", top=120, bottom=100)]
ltf_fvgs = [make_fvg("bullish_fvg", top=125, bottom=105)]  # top exceeds HTF top
result = detect_nested_fvgs(htf_fvgs, ltf_fvgs)
results.append(run_test("LTF partially outside HTF range -> no nesting", result, expected_count=0))

# --- Test 4: LTF FVG exactly equal to HTF range -> still counts as nested (boundary inclusive) ---
htf_fvgs = [make_fvg("bullish_fvg", top=120, bottom=100)]
ltf_fvgs = [make_fvg("bullish_fvg", top=120, bottom=100)]
result = detect_nested_fvgs(htf_fvgs, ltf_fvgs)
results.append(run_test("LTF equal to HTF range -> nested (boundary inclusive)", result, expected_count=1, expected_same_direction=True))

# --- Test 5: multiple LTF FVGs, only some nested ---
htf_fvgs = [make_fvg("bullish_fvg", top=120, bottom=100)]
ltf_fvgs = [
    make_fvg("bullish_fvg", top=112, bottom=105),   # nested
    make_fvg("bullish_fvg", top=95, bottom=90),      # not nested (outside range entirely)
]
result = detect_nested_fvgs(htf_fvgs, ltf_fvgs)
results.append(run_test("Mixed LTF list -> only the contained one nests", result, expected_count=1, expected_same_direction=True))

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")