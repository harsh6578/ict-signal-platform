from core.database import SessionLocal
from models.symbol import Symbol
from models.timeframe import Timeframe


TIMEFRAMES_TO_SEED = [
    {"code": "1m", "label": "1 Minute", "minutes": 1},
    {"code": "5m", "label": "5 Minutes", "minutes": 5},
    {"code": "15m", "label": "15 Minutes", "minutes": 15},
    {"code": "1h", "label": "1 Hour", "minutes": 60},
    {"code": "4h", "label": "4 Hours", "minutes": 240},
    {"code": "1d", "label": "1 Day", "minutes": 1440},
]


def seed_initial_data():
    db = SessionLocal()
    try:
        # Add BTCUSDT symbol if it doesn't already exist
        existing_symbol = db.query(Symbol).filter(Symbol.code == "BTCUSDT").first()
        if not existing_symbol:
            symbol = Symbol(code="BTCUSDT", base_asset="BTC", quote_asset="USDT")
            db.add(symbol)
            print("Added symbol: BTCUSDT")
        else:
            print("Symbol BTCUSDT already exists, skipping.")

        # Add all common timeframes if they don't already exist
        for tf in TIMEFRAMES_TO_SEED:
            existing_timeframe = db.query(Timeframe).filter(Timeframe.code == tf["code"]).first()
            if not existing_timeframe:
                timeframe = Timeframe(code=tf["code"], label=tf["label"], minutes=tf["minutes"])
                db.add(timeframe)
                print(f"Added timeframe: {tf['code']}")
            else:
                print(f"Timeframe {tf['code']} already exists, skipping.")

        db.commit()
        print("Seed data committed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_initial_data()