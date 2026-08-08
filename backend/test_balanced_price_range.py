"""
Test script for detect_balanced_price_range().
Run from the backend/ directory: python3 test_balanced_price_range.py

Uses lightweight synthetic FVG dicts (only the keys the function reads:
type, top, bottom, candle_3) so tests are fully deterministic and don't
depend on the database.
"""

from services.ict_engine.concepts.fair_value_gaps import detect_balanced_price_range


def make_fvg(fvg_type, top, bottom):
    return {
        "type": fvg_type,
        "top": top,
        "bottom": bottom,
        "midpoint": (top + bottom) / 2,
        "candle_3": None,
    }


def run_test(name, actual_list, expected_count, expected_type=None, expected_top=None, expected_bottom=None):
    passed = len(actual_list) == expected_count
    if passed and expected_count > 0:
        bpr = actual_list[0]
        if expected_type is not None:
            passed = passed and bpr["type"] == expected_type
        if expected_top is not None:
            passed = passed and bpr["top"] == expected_top
        if expected_bottom is not None:
            passed = passed and bpr["bottom"] == expected_bottom

    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    found {len(actual_list)} BPR(s)")
    for bpr in actual_list:
        print(f"    type={bpr['type']}  top={bpr['top']}  bottom={bpr['bottom']}  midpoint={bpr['midpoint']}")
    if not passed:
        print(f"    expected: count={expected_count}  type={expected_type}  top={expected_top}  bottom={expected_bottom}")
    return passed


results = []

# --- Test 1: bearish FVG then bullish FVG overlapping -> bullish_bpr ---
fvgs = [
    make_fvg("bearish_fvg", top=110, bottom=100),
    make_fvg("bullish_fvg", top=106, bottom=98),
]
bprs = detect_balanced_price_range(fvgs)
results.append(run_test(
    "Bearish then bullish FVG - overlap forms bullish_bpr",
    bprs, expected_count=1, expected_type="bullish_bpr", expected_top=106, expected_bottom=100
))

# --- Test 2: bullish FVG then bearish FVG overlapping -> bearish_bpr ---
fvgs = [
    make_fvg("bullish_fvg", top=110, bottom=100),
    make_fvg("bearish_fvg", top=106, bottom=98),
]
bprs = detect_balanced_price_range(fvgs)
results.append(run_test(
    "Bullish then bearish FVG - overlap forms bearish_bpr",
    bprs, expected_count=1, expected_type="bearish_bpr", expected_top=106, expected_bottom=100
))

# --- Test 3: no overlap -> no BPR ---
fvgs = [
    make_fvg("bullish_fvg", top=110, bottom=105),
    make_fvg("bearish_fvg", top=104, bottom=95),
]
bprs = detect_balanced_price_range(fvgs)
results.append(run_test(
    "No price overlap - no BPR",
    bprs, expected_count=0
))

# --- Test 4: same type FVGs - should never form a BPR regardless of overlap ---
fvgs = [
    make_fvg("bullish_fvg", top=110, bottom=100),
    make_fvg("bullish_fvg", top=106, bottom=98),
]
bprs = detect_balanced_price_range(fvgs)
results.append(run_test(
    "Same-type FVGs (both bullish) - no BPR",
    bprs, expected_count=0
))

# --- Test 5: edge touching exactly (overlap_top == overlap_bottom) - not a valid overlap ---
fvgs = [
    make_fvg("bullish_fvg", top=110, bottom=100),
    make_fvg("bearish_fvg", top=100, bottom=90),
]
bprs = detect_balanced_price_range(fvgs)
results.append(run_test(
    "Exact edge touch (no real overlap) - no BPR",
    bprs, expected_count=0
))

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")