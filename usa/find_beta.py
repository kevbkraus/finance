
# find_beta.py ------------------------------------------------------------------------------------
#   Compares direct estimation of CAPM beta with regression beta 
#   Note: To find regression beta in the same way as yahoo finance does - run a regression on 60 
# recent monthly returns of SP500 and a given stock
# -------------------------------------------------------------------------------------------------
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import sklearn.metrics as metrics
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import date, datetime

import argparse

# Parse arguments
msg = "Finds CAPM beta using the same method as used by yahoo finance"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('stock_ticker', help='stock ticker symbol (Ex. AAPL, GOOG, MSFT etc.)')
parser.add_argument('-rf', '--risk_free_rate', help='Risk free rate (percentage) ex 4.35', type=float)
parser.add_argument('-start_date', help='start date in yyyy-MM-dd format ex 2020-1-1', type=str)
parser.add_argument('-end_date', help='end_date in yyyy-MM-dd format ex 2022-12-1', type=str)

args = parser.parse_args()
stock_ticker = args.stock_ticker
if args.risk_free_rate:
    rf = args.risk_free_rate/100
else:
    rf = 0.02

# Set parameters
# sometimes better to look at the beta over a specific time period and remove anomalous periods
# (such as COVID market in 2020 and 2021).
start = datetime(2016, 12, 2)
end = date.today()

if args.start_date:
    start_str = args.start_date.split('-')
    start = datetime(int(start_str[0]), int(start_str[1]), int(start_str[2]))
if args.end_date:
    end_str = args.end_date.split('-')
    end = datetime(end_str[2], end_str[0], end_str[1])

start_str = datetime.strftime(start, format='%Y-%m-%d')
end_str = datetime.strftime(end, format='%Y-%m-%d')

# Main code
SP500 = pd.DataFrame((yf.download('^GSPC', start = start_str, end = end_str, group_by='ticker')).Close)
stock = pd.DataFrame((yf.download(stock_ticker, start = start_str, end = end_str, group_by='ticker')).Close)

# Hypothesis: Expected returns and risks are stationary
SP500_monthly = SP500.resample('M').last()
SP500_monthly['monthly return'] = SP500_monthly['Close'].pct_change(periods=1)    # Monthly returns calculated every month 

stock_monthly = stock.resample('M').last()
stock_monthly['monthly return'] = stock_monthly['Close'].pct_change(periods=1)

new_df = pd.DataFrame(SP500_monthly['monthly return'])
new_df = new_df.join(stock_monthly['monthly return'], lsuffix=' sp500',rsuffix=' stock')
new_df.dropna(inplace=True)

# Find beta by directly estimating cov(stock, sp500) and var(sp500)
stacked_mat = np.stack((new_df['monthly return stock'].values[1:], new_df['monthly return sp500'].values[1:]), axis=0)
cov_mat = np.cov(stacked_mat)
beta = cov_mat[0,1]/cov_mat[1,1]
print("Directly estimated beta:", beta)

# Perform regression and find beta
model = LinearRegression()
x = new_df['monthly return sp500'].values[1:].reshape((-1,1))
y = new_df['monthly return stock'].values[1:]
x = x - rf/12   # Subtract risk free monthly rate (treat rf like an APR
y = y - rf/12
model.fit(x,y)
p = model.predict(x)

# Visualization
fig1,ax1 = plt.subplots()
ax1.scatter(x, y, color='black')
ax1.plot(x, p, color='blue', linewidth=3)
ax1.set_xlabel('SP500')
ax1.set_ylabel(stock_ticker)

lrfit_details = "r-squared: %.2f, \nmse: %.4f, \n\nbeta: %.2f, \nalpha: %.2f"\
                              %(metrics.r2_score(y,p),\
                                metrics.mean_squared_error(y,p),\
                                model.coef_,\
                                model.intercept_)

plt.text(x = 0.1, y = 0.9, s = lrfit_details, transform=ax1.transAxes,  
            horizontalalignment = "left", verticalalignment = "top", fontsize = 12)   
plt.show()
