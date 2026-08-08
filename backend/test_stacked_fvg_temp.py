"""
Temporary test script for detect_stacked_fvgs().
Run from backend/: python3 test_stacked_fvg_temp.py
Delete after validation - not a permanent regression test.
"""

from services.ict_engine.concepts.fair_value_gaps import detect_stacked_fvgs


def make_fvg(fvg_type, top, bottom):
    return {"type": fvg_type, "top": top, "bottom": bottom, "midpoint": (top + bottom) / 2}


def run_test(name, actual_list, expected_count, expected_stack_len=None):
    passed = len(actual_list) == expected_count
    if passed and expected_count > 0 and expected_stack_len is not None:
        passed = passed and len(actual_list[0]["fvgs"]) == expected_stack_len

    status_label = "PASS" if passed else "FAIL"
    print(f"[{status_label}] {name}")
    print(f"    found {len(actual_list)} stack(s)")
    for stack in actual_list:
        print(f"    type={stack['type']}  size={len(stack['fvgs'])}  entry_ce={stack['entry_fvg']['midpoint']}  top={stack['top']}  bottom={stack['bottom']}")
    if not passed:
        print(f"    expected: count={expected_count}  stack_len={expected_stack_len}")
    return passed


results = []

# --- Test 1: 3 consecutive bullish FVGs -> one stack of 3 ---
fvgs = [
    make_fvg("bullish_fvg", top=105, bottom=100),
    make_fvg("bullish_fvg", top=112, bottom=107),
    make_fvg("bullish_fvg", top=120, bottom=114),
]
stacks = detect_stacked_fvgs(fvgs)
results.append(run_test("3 consecutive bullish FVGs -> 1 stack of 3", stacks, expected_count=1, expected_stack_len=3))

# --- Test 2: bullish-bearish-bullish -> broken sequence, no stack ---
fvgs = [
    make_fvg("bullish_fvg", top=105, bottom=100),
    make_fvg("bearish_fvg", top=104, bottom=98),
    make_fvg("bullish_fvg", top=110, bottom=106),
]
stacks = detect_stacked_fvgs(fvgs)
results.append(run_test("Bullish-bearish-bullish -> no stack (each run len 1)", stacks, expected_count=0))

# --- Test 3: single isolated FVG -> no stack ---
fvgs = [make_fvg("bullish_fvg", top=105, bottom=100)]
stacks = detect_stacked_fvgs(fvgs)
results.append(run_test("Single FVG -> no stack", stacks, expected_count=0))

# --- Test 4: 2 bearish then 2 bullish -> two separate stacks ---
fvgs = [
    make_fvg("bearish_fvg", top=105, bottom=100),
    make_fvg("bearish_fvg", top=99, bottom=94),
    make_fvg("bullish_fvg", top=110, bottom=106),
    make_fvg("bullish_fvg", top=116, bottom=111),
]
stacks = detect_stacked_fvgs(fvgs)
passed = len(stacks) == 2 and len(stacks[0]["fvgs"]) == 2 and len(stacks[1]["fvgs"]) == 2
status_label = "PASS" if passed else "FAIL"
print(f"[{status_label}] 2 bearish + 2 bullish -> two stacks of 2")
for s in stacks:
    print(f"    type={s['type']}  size={len(s['fvgs'])}")
results.append(passed)

print()
total = len(results)
passed_count = sum(results)
print(f"Summary: {passed_count}/{total} tests passed")