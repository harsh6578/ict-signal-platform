"""
Test script for score_fvg_context(). Run from backend/: python3 test_fvg_context_score_temp.py
"""

from services.ict_engine.concepts.fair_value_gaps import score_fvg_context


class MockCandle:
    def __init__(self):
        pass


def make_fvg(quality=None, is_aligned=None):
    c1, c3 = MockCandle(), MockCandle()
    fvg = {"type": "bullish_fvg", "top": 110, "bottom": 100, "midpoint": 105, "candle_1": c1, "candle_3": c3}
    if quality is not None:
        fvg["quality"] = quality
    if is_aligned is not None:
        fvg["is_aligned"] = is_aligned
    return fvg


def run_test(name, actual, expected_score):
    passed = actual["confluence_score"] == expected_score
    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    score={actual['confluence_score']}  factors={actual['confluence_factors']}")
    if not passed:
        print(f"    expected score={expected_score}")
    return passed


results = []

# Test 1: exceptional + aligned + in a stack -> 2 + 1 + 1 = 4
fvg = make_fvg(quality="exceptional", is_aligned=True)
stacks = [{"fvgs": [fvg]}]
result = score_fvg_context(fvg, stacks=stacks)
results.append(run_test("Exceptional + aligned + stacked -> 4", result, 4))

# Test 2: weak + not aligned + no confluences -> 0
fvg = make_fvg(quality="weak", is_aligned=False)
result = score_fvg_context(fvg)
results.append(run_test("Weak + not aligned + no confluence -> 0", result, 0))

# Test 3: part of a BPR -> +2
fvg = make_fvg()
bprs = [{"source_fvg_1": fvg, "source_fvg_2": make_fvg()}]
result = score_fvg_context(fvg, bprs=bprs)
results.append(run_test("Part of BPR -> 2", result, 2))

# Test 4: nested same-direction -> +2
fvg = make_fvg()
nested_pairs = [{"htf_fvg": fvg, "ltf_fvg": make_fvg(), "same_direction": True}]
result = score_fvg_context(fvg, nested_pairs=nested_pairs)
results.append(run_test("Nested same-direction -> 2", result, 2))

# Test 5: nested opposite-direction -> +1
fvg = make_fvg()
nested_pairs = [{"htf_fvg": fvg, "ltf_fvg": make_fvg(), "same_direction": False}]
result = score_fvg_context(fvg, nested_pairs=nested_pairs)
results.append(run_test("Nested opposite-direction -> 1", result, 1))

# Test 6: all confluences combined -> 2+1+1+2+2 = 8
fvg = make_fvg(quality="exceptional", is_aligned=True)
stacks = [{"fvgs": [fvg]}]
nested_pairs = [{"htf_fvg": fvg, "ltf_fvg": make_fvg(), "same_direction": True}]
bprs = [{"source_fvg_1": fvg, "source_fvg_2": make_fvg()}]
result = score_fvg_context(fvg, stacks=stacks, nested_pairs=nested_pairs, bprs=bprs)
results.append(run_test("All confluences combined -> 8", result, 8))

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")