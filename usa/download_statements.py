# download_statements.py -------------------------------------------------------------------------------
#   Downloads financial statements, flags errors, converts data to convenient formats and store in files
#
# ------------------------------------------------------------------------------------------------------

import requests
import json
import numpy as np
import pandas as pd

import os
import sys
import errno
from tqdm import tqdm, trange
import argparse

# Parameters
AV_URL = "https://www.alphavantage.co/query"
AV_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Parse command line arguments
msg = "Downloads financial statements"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-t', '--ticker', help="ticker symbol")
parser.add_argument('-s', '--sector', help="GICS sector exactly as given in Wikipedia - List_of S&P 500 companies")
parser.add_argument('-r', '--sample_size', help='Sample size. If not supplied, all pertinent stocks will be taken into consideration', type=int)
help_text = """Forcefully update non-price data (Ex. net income). If not supplied, preexising (possibly outdated)
               data will be used when available """ 
parser.add_argument('-f', '--update_data', help=help_text)
parser.add_argument('statement', help="income_statement or balance_sheet", choices=['income_statement', 'balance_sheet'])

args = parser.parse_args()
if args.ticker:                 # If the user explicityly gives ticker symbol, then sector, update_data, sample_size are irrelevant 
    symbols = list()
    symbols.append(args.ticker)
    args.update_data = True
else:
    sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
    
    if args.sector: 
        sublist = sp500_list[sp500_list['GICS Sector']==args.sector]
    else:   # all sectors
        sublist = sp500_list
        
    if args.sample_size:
        sublist = sublist.sample(args.sample_size)

    symbols = list(sublist['Symbol'].values)

if args.statement == 'income_statement':
    subfolder = 'income_statements'
    av_function = 'INCOME_STATEMENT'
else:   # This is the only other possibility because argparser already restritics the -
        # choices and produces error if user gives something outside that
    subfolder = 'balance_sheets'
    av_function = 'BALANCE_SHEET'

# Main code
for symbol in tqdm(symbols, desc='Progress'):
    annual_stmt_filename = consolidated_prices_folder + '/' + subfolder + '/' + symbol + '_annual.csv'
    quart_stmt_filename = consolidated_prices_folder + '/' + subfolder + '/' + symbol + '_quarterly.csv'

    if (not args.update_data) and os.path.exists(annual_stmt_filename): # if file already exists and 
                                                                        # forceful update is not enabled, skip to next symbol 
        continue        # It is enough to check if annual statement exists - quarterly can be safely assumed to exist if annual does

    query_params = { "function": av_function, "symbol": symbol, "apikey": AV_KEY}
    response = (requests.get(AV_URL, params=query_params)).json()
    
    # Error checks
    if not response: #If there is no response 
        print('Empty response received for ', symbol)
        continue

    if response['symbol'] != symbol: # This shouldn't happen. But we double check
        print('Alpha vantage returned wrong data. Expected: ', symbol, '. Got: ', response['symbol'])
        sys.exit(errno.EIO)

    statement_annual = pd.DataFrame(response['annualReports'])
    statement_quart = pd.DataFrame(response['quarterlyReports'])
    
    #statement_annual['fiscalDateEnding'] = pd.to_datetime(bl_sheet_annual['fiscalDateEnding'])
    statement_annual.set_index('fiscalDateEnding', inplace=True)
    statement_quart.set_index('fiscalDateEnding', inplace=True)

    statement_annual.to_csv(annual_stmt_filename)
    statement_quart.to_csv(quart_stmt_filename)


    
