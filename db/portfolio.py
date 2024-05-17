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
    engine = create_engine("sqlite:///../gsb.db")
    with Session(engine) as session:
        capital_values = []
        capital_value = 100
        prices_stmt = select(AssetDailyPrice).where(AssetDailyPrice.ticker.in_(["SPHY"]))
        prices = session.scalars(prices_stmt).all()
        shares = capital_value / prices[0].adj_close
        print("starting shares ", shares)

        # start date - 4-19-12
        rates = np.array([2.1, 1, 0.9, 1.4, 2.35, 3.3, 3.9, 4.25])
        days_per_rate = np.array([486, 674, 43, 90, 140, 145, 95, 238])
        initial_savings = capital_value
        savings_values = [initial_savings]

        for rate, days in zip(rates, days_per_rate):
            daily_rate = rate / 365  # Convert annual rate to daily rate
            compounded_rate = (1 + (daily_rate / 100)) ** days  # Calculate compounded rate for the specific period
            new_value = savings_values[-1] * compounded_rate
            savings_values.append(new_value)

        price_hist = []
        # 3.9 to 4.25
        for price in prices:
            capital_values.append(price.adj_close * shares)

        x = np.arange(1, len(prices) + 1)
        xtwo = np.arange(1, len(prices) + 1)
        print(capital_values)
        # Create the scatter plot
        plt.scatter(x, capital_values, color='blue', marker='o')

        # Customizing the plot
        plt.title('Scatter Plot Example')
        plt.xlabel('Index')
        plt.ylabel('Values')

        # Show the plot
        plt.show()


stock_return()