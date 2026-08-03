class MarketContext:
    """
    Shared 'blackboard' object passed between ICT concept modules.

    Holds the raw candle data for a symbol + timeframe, plus a place
    for concept modules to store their findings so later modules can
    build on earlier ones (e.g. dealing_range needs market_structure's
    swing high/low first).
    """

    def __init__(self, symbol_code: str, timeframe_code: str, candles: list):
        self.symbol_code = symbol_code
        self.timeframe_code = timeframe_code
        self.candles = candles  # list of Candle model instances, oldest to newest

        # Results detected so far, keyed by concept code (e.g. "EXTERNAL_SWINGS")
        self.results = {}

    def set_result(self, concept_code: str, result):
        """
        Stores a complete result (e.g. a whole list of swings) under
        the given concept code, replacing any previous value.
        """
        self.results[concept_code] = result

    def get_results(self, concept_code: str):
        return self.results.get(concept_code, [])