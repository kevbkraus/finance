
# research_stock.py -------------------------------------------------------------------------------
#   Researches a stock by its fundamentals, ratios 
#
# -------------------------------------------------------------------------------------------------

import requests
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import sklearn.metrics as metrics
import matplotlib.pyplot as plt

import os
import sys
import errno
import argparse

# Parse command line arguments
msg = 'Researches a stock by its fundamentals, ratios'
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('symbol', help='Stock symbol')

args = parser.parse_args()
symbol = args.symbol

# Parameters
AV_URL = "https://www.alphavantage.co/query"
AV_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Main code
filename = consolidated_prices_folder + '/' + symbol + '.csv'
if not os.path.exists(filename): 
    print("Sorry stock daily prices isn't available. Download it first")
    sys.exit(errno.EIO)

# Get price data
try:    
    prices = pd.read_csv(filename, index_col=0, parse_dates=True)
except Exception as e:
    print("Error while trying to open stock data for ", symbol, " Error: ", e)
    sys.exit(errno.EIO)

# Get fundamentals
# INCOME STATEMENT
query_params = { "function": "INCOME_STATEMENT", "symbol": symbol, "apikey": AV_KEY}
response = (requests.get(AV_URL, params=query_params)).json()
if response['symbol'] != symbol:
    print('Alpha vantage returned wrong data. Expected: ', symbol, '. Got: ', response['symbol'])
    sys.exit(errno.EIO)

inc_stmt_annual = pd.DataFrame(response['annualReports'])
inc_stmt_quart = pd.DataFrame(response['quarterlyReports'])

inc_stmt_annual['fiscalDateEnding'] = pd.to_datetime(inc_stmt_annual['fiscalDateEnding'])
inc_stmt_annual.set_index('fiscalDateEnding', inplace=True)
inc_stmt_annual.to_csv('temp.csv')                                      # This jugaad of writing to csv and reading back 
inc_stmt_annual = pd.read_csv('temp.csv', index_col=0, parse_dates=True)    # is done to convert numbers originally parsed as
                                                                        # strings to correctly be parsed as numbers

inc_stmt_quart['fiscalDateEnding'] = pd.to_datetime(inc_stmt_quart['fiscalDateEnding'])
inc_stmt_quart.set_index('fiscalDateEnding', inplace=True)
inc_stmt_quart.to_csv('temp.csv')
inc_stmt_quart = pd.read_csv('temp.csv', index_col=0, parse_dates=True)

# BALANCE SHEETS 
query_params = { "function": "BALANCE_SHEET", "symbol": symbol, "apikey": AV_KEY}
response = (requests.get(AV_URL, params=query_params)).json()
if response['symbol'] != symbol:
    print('Alpha vantage returned wrong data. Expected: ', symbol, '. Got: ', response['symbol'])
    sys.exit(errno.EIO)

bl_sheet_annual = pd.DataFrame(response['annualReports'])
bl_sheet_quart = pd.DataFrame(response['quarterlyReports'])

bl_sheet_annual['fiscalDateEnding'] = pd.to_datetime(bl_sheet_annual['fiscalDateEnding'])
bl_sheet_annual.set_index('fiscalDateEnding', inplace=True)
bl_sheet_annual.to_csv('temp.csv')
bl_sheet_annual = pd.read_csv('temp.csv', index_col=0, parse_dates=True)

bl_sheet_quart['fiscalDateEnding'] = pd.to_datetime(bl_sheet_quart['fiscalDateEnding'])
bl_sheet_quart.set_index('fiscalDateEnding', inplace=True)
bl_sheet_quart.to_csv('temp.csv')
bl_sheet_quart = pd.read_csv('temp.csv', index_col=0, parse_dates=True)


# Visualisation
fig1,ax1 = plt.subplots()
fig1.suptitle('Price vs. Net income')
pcolor = 'tab:blue'
ax1.set_xlabel('date')
ax1.set_ylabel('price (USD)', color=pcolor)
ax1.plot(prices['Close'], color=pcolor)
ax1.tick_params(axis='y', labelcolor=pcolor)

ax2 = ax1.twinx()
pcolor = 'tab:red'
ax2.set_ylabel('net income (million USD)', color=pcolor)
ax2.plot(inc_stmt_annual['netIncome']/1000000, color=pcolor, marker='o')
ax2.tick_params(axis='y', labelcolor=pcolor)

fig2,ax3 = plt.subplots()
fig2.suptitle('Price vs. Net income')
pcolor = 'tab:blue'
ax3.set_xlabel('date')
ax3.set_ylabel('price (USD)', color=pcolor)
ax3.plot(prices['Close'].loc[inc_stmt_quart.index[-1]:], color=pcolor)
ax3.tick_params(axis='y', labelcolor=pcolor)

ax4 = ax3.twinx()
pcolor = 'tab:red'
ax4.set_ylabel('net income (million USD)', color=pcolor)
ax4.plot(inc_stmt_quart['netIncome']/1000000, color=pcolor, marker='o')
ax4.tick_params(axis='y', labelcolor=pcolor)

plt.show()
