
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

# BALANCE SHEETS 
query_params = { "function": "BALANCE_SHEET", "symbol": symbol, "apikey": AV_KEY}
response = (requests.get(AV_URL, params=query_params)).json()
if response['symbol'] != symbol:
    print('Alpha vantage returned wrong data. Expected: ', symbol, '. Got: ', response['symbol'])
    sys.exit(errno.EIO)

bl_sheet_annual = pd.DataFrame(response['annualReports'])
bl_sheet_quart = pd.DataFrame(response['quarterlyReports'])



