# portfolio.py -----------------------------------------------------------------------------------------
#   Examines performance of a portfolio of one or more stocks.
# -------------------------------------------------------------------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from context import *
from sqlalchemy import select
import matplotlib.pyplot as plt
import numpy as np

# Looks at stock price over time
def stock_price():
    pass

# Looks at stock price + reinvested dividends over time
def stock_return():
    engine = create_engine("sqlite:///../gsb.db", echo=True)
    with Session(engine) as session:
        capital_values = []
        capital_value = 1000
        prices_stmt = select(AssetDailyPrice).where(AssetDailyPrice.ticker.in_(["SPHY"]))
        dividends_dates_subquery = select(AssetDividends).where(AssetDividends.ticker.in_(["SPHY"])).subquery()
        prices = session.scalars(prices_stmt).all()
        shares = capital_value / prices[0].close
        for price in prices:
            # Check if the date exists in the dividends dates subquery
            if session.query(dividends_dates_subquery).filter(dividends_dates_subquery.c.date == price.date).first():
                # Retrieve the corresponding dividend entry for further use
                dividend_entry = session.query(AssetDividends).filter(AssetDividends.ticker == "SPHY",
                                                                      AssetDividends.date == price.date).first()
                if dividend_entry:
                    payout = shares * dividend_entry.dividend_per_share
                    shares_purchased = payout / price.close
                    shares = shares + shares_purchased
            capital_values.append(price.close * shares)

        x = np.arange(1, len(capital_values) + 1)

        # Create the scatter plot
        plt.scatter(x, capital_values, color='blue', marker='o')

        # Customizing the plot
        plt.title('Scatter Plot Example')
        plt.xlabel('Index')
        plt.ylabel('Values')

        # Show the plot
        plt.show()


stock_return()