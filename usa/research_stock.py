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

# Parameters
FMP_URL = "https://financialmodelingprep.com/api/v3"
FMP_KEY = os.environ.get('FMP_API_KEY')
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Parse command line arguments
msg = 'Researches a stock by its fundamentals, ratios'
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-s', '--symbol', help='Stock symbol')
arghelp = """Give a GICS sector name exactly as in https://en.wikipedia.org/wiki/List_of_S%26P_500_companies. A  
           random recurity will be chosen from this sector. Note that if -s argument is supplied, this 
           argument is ignored."""
parser.add_argument('-i', '--sector', help=arghelp)

args = parser.parse_args()
if args.symbol:
    symbol = args.symbol
    sector = 'none'
elif args.sector: # This gets processed only if no symbol is explicitly given
    sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
    sublist = sp500_list[sp500_list['GICS Sector']==args.sector]
    symbol = sublist.sample()['Symbol'].values[0]
    sector = args.sector
else:
    sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
    sample_df = sp500_list.sample()
    symbol = sample_df['Symbol'].values[0]
    sector = sample_df['GICS Sector'].values[0]

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
URL_SUFFIX = '/income-statement/' + symbol
query_params = {'limit': 120, 'apikey': FMP_KEY}
response = (requests.get(FMP_URL+URL_SUFFIX, params=query_params)).json()
if response[0]['symbol'] != symbol:
    print('Alpha vantage returned wrong data. Expected: ', symbol, '. Got: ', response['symbol'])
    sys.exit(errno.EIO)

inc_stmt_annual = pd.DataFrame(response)
inc_stmt_annual['date'] = pd.to_datetime(inc_stmt_annual['date']).dt.date
inc_stmt_annual.set_index('date', inplace=True)

# Visualisation
fig1,ax1 = plt.subplots()
fig1.suptitle(symbol + ' (' + sector + ')')
pcolor = 'tab:blue'
ax1.set_xlabel('date')
ax1.set_ylabel('price (USD)', color=pcolor)
ax1.plot(prices['Close'], color=pcolor)
ax1.tick_params(axis='y', labelcolor=pcolor)
ax1.grid(True, axis='both')

ax2 = ax1.twinx()
pcolor = 'tab:red'
ax2.set_ylabel('net income (million USD)', color=pcolor)
ax2.plot(inc_stmt_annual['netIncome']/1000000, color=pcolor, marker='o')
ax2.tick_params(axis='y', labelcolor=pcolor)

ax1.set_xticks(inc_stmt_annual.index)
ax1.set_xticklabels(inc_stmt_annual.index, rotation = 90)
#ax2.grid(True, axis='both')

plt.show()
