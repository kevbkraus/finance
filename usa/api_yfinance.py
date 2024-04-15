# Wrapper for yfinance api
import yfinance as yf


# Retrieves prices and dividends for the given ticker
def run(ticker: str):
    t = yf.Ticker(ticker)

    # get all stock info
    t.info

    # get historical market data
    hist = t.history(period="1mo")
    print(hist)