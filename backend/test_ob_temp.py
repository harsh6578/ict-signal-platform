from services.ict_engine.concepts.fair_value_gaps import detect_fair_value_gaps
from services.ict_engine.concepts.order_blocks import detect_order_blocks


class MockCandle:
    def __init__(self, o, h, l, c):
        self.open_price = o
        self.high_price = h
        self.low_price = l
        self.close_price = c


candles = [
    MockCandle(105, 104, 100, 101),
    MockCandle(101, 103, 100, 102),
    MockCandle(107, 112, 108, 110),
]

fvgs = detect_fair_value_gaps(candles)
print("FVGs found:", len(fvgs))

obs = detect_order_blocks(candles, fvgs)
print("Order Blocks found:", len(obs))
for ob in obs:
    print(ob["type"], "top=", ob["top"], "bottom=", ob["bottom"])

from services.ict_engine.concepts.order_blocks import check_order_block_status

class MockCandle2:
    def __init__(self, l, h, c):
        self.low_price = l
        self.high_price = h
        self.close_price = c

ob = {"type": "bullish_ob", "top": 110, "bottom": 100}

# wick into zone, body holds -> mitigated
test_candles_1 = [MockCandle2(105, 112, 107)]
result1 = check_order_block_status(ob, test_candles_1, ob_index=-1)
print("Test 1 (expect mitigated):", result1["status"])

# body closes below bottom -> breaker
test_candles_2 = [MockCandle2(98, 108, 97)]
result2 = check_order_block_status(ob, test_candles_2, ob_index=-1)
print("Test 2 (expect breaker):", result2["status"])