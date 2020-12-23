# download_yinfo.py -------------------------------------------------------------------------------
#   Downloads yahoo stock information such as beta, financial ratios, company information
#
# -------------------------------------------------------------------------------------------------

import requests
import json
import numpy as np
import pandas as pd
import yfinance 

import os
import sys
import errno
from tqdm import tqdm, trange
import argparse

# Parameters
yinfo_filename = '/home/dinesh/Documents/security_prices/usa/yinfo.csv'

# Parse command line arguments
msg = "Downloads yahoo stock information such as beta, financial ratios, company information"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-t', '--ticker', help="ticker symbol")
parser.add_argument('-s', '--sector', help="GICS sector exactly as given in Wikipedia - List_of S&P 500 companies")
parser.add_argument('-r', '--sample_size', help='Sample size. If not supplied, all pertinent stocks will be taken into consideration. Default = 50', type=int)
help_text = """Forcefully update non-price data (Ex. net income). If not supplied, preexising (possibly outdated)
               data will be used when available """ 
parser.add_argument('-f', '--update_data', help=help_text)

args = parser.parse_args()
if args.ticker:                 # If the user explicityly gives ticker symbol, then sector, update_data, sample_size are irrelevant 
    symbols = list()
    symbols.append(args.ticker)
    args.update_data = True
else:
    sp500_list = pd.read_csv('/home/dinesh/Documents/security_prices/usa/download_log.csv')
    
    if args.sector: 
        sublist = sp500_list[sp500_list['GICS Sector']==args.sector]
    else:   # all sectors
        sublist = sp500_list
        
    if args.sample_size:
        sublist = sublist.sample(args.sample_size)

    symbols = list(sublist['Symbol'].values)

# Main code
if not os.path.exists(yinfo_filename):
    compiled_info_df = pd.DataFrame()
else:
    compiled_info_df = pd.read_csv(yinfo_filename)

if not compiled_info_df.empty:
    if args.update_data:
        for symbol in symbols:
            compile_info_df = compiled_info_df[compiled_info_df['symbol'] == symbol]
    else:
        for symbol in symbols:
            if symbol in compiled_info_df['symbol'].values:
                symbols.remove(symbol) # To remove unnecessary calls to yfinance

for symbol in tqdm(symbols, desc='Progress'):
    ticker = yfinance.Ticker(symbol)
    info_dict = ticker.info
    if 'longBusinessSummary' in info_dict:
        info_dict.pop('longBusinessSummary') 
    compiled_info_df = compiled_info_df.append(info_dict, ignore_index=True)

compiled_info_df.set_index('symbol', inplace=True)
compiled_info_df.to_csv(yinfo_filename)
