import yfinance as yf
import importlib
import context
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

importlib.reload(context)
from context import AssetDividends
from context import AssetDailyPrice

def initialize_ticker(ticker: str):
    # Retrieves prices and dividends for the given ticker
    t = yf.Ticker(ticker)

    # Info - t.info

    # get historical market data
    hist = t.history(period="5y")

    engine = create_engine("sqlite:///../gsb.db")

    # Initialize prices and dividends. Commit at end.
    with Session(engine) as session:
        for index, row in hist.iterrows():
            asset_hist = AssetDailyPrice(
                ticker = ticker,
                date = str(index)[:10],
                close = round(row["Close"], 2)
            )
            session.add(asset_hist)
            dividend = round(row["Dividends"], 2)
            if (dividend > 0):
                asset_div = AssetDividends(
                    ticker = ticker,
                    date = str(index)[:10],
                    dividend_per_share = dividend
                )
                session.add(asset_div)
        session.commit()