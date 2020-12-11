
# get_sp500.py -----------------------------------------------------------------------------------------
#  Gets stock prices of S&P500 stocks and stores them locally  
#
# -------------------------------------------------------------------------------------------------
import pandas as pd
import yfinance as yf
from datetime import date, datetime

import os
import sys
import errno
import argparse

# Parse arguments
msg = "Gets SP500 data"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-s', '--start_date', help='Start date as a string in %Y-%m-%d format (Default: 1990-01-31)')
parser.add_argument('-e', '--end_date', help='End date as a string in %Y-%m-%d format (Default: today)')

args = parser.parse_args()
if args.start_date:
    start_str = start_date
else:
    start = datetime(1990, 1, 31)
    start_str = datetime.strftime(start, format='%Y-%m-%d')

if args.start_date:
    end_str = end_date
else:
    end = date.today()
    end_str = datetime.strftime(end, format='%Y-%m-%d')

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Main code
SP500 = yf.download('^GSPC', start = start_str, end = end_str, group_by='ticker')
SP500.to_csv(consolidated_prices_folder + '/sp500.csv')

sp500_table=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
sp500_df = sp500_table[0] # TODO: Convert this to a dataframe using pd.DataFrame and remove index while storing
sp500_df['download status'] = 'not done'

# Loop through SP500 symbols
symbols = sp500_df['Symbol']
count = 0
for symbol in symbols:
    filename = consolidated_prices_folder + '/' + symbol + '.csv'
    if os.path.exists(filename):
        print('File exists: skipping ', symbol)
        sp500_df.loc[sp500_df.Symbol == symbol, 'download_status'] = 'skipped'
        continue
    else:
        try:
            symbol_df = yf.download(symbol, start = start_str, end = end_str, group_by='ticker')
        except Exception as e:
            print("Error while trying to download symbol: ", symbol, " Error: ", e)
            sp500_df.loc[sp500_df.Symbol == symbol, 'download_status'] = 'error'
            continue

        sp500_df.loc[sp500_df.Symbol == symbol, 'download_status'] = 'done'
        symbol_df.to_csv(filename)
        count = count+1
        print(count, " of ", len(symbols), " done")
 
sp500_df.to_csv(consolidated_prices_folder + '/download_log.csv')



