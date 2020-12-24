# corr_mat.py -------------------------------------------------------------------------------------
#   Generates correlation matrix and risk-return tables on annual returns of SP500 stocks
# 
# -------------------------------------------------------------------------------------------------

import requests
import math
import numpy as np
import pandas as pd

import os
import sys
from tqdm import tqdm, trange
import argparse

# Function definitions
# calc_returns ------------------------------------------------------------------------------------
#   Calculates annual returns with a granularity of a month
#
# Inputs:
#   prices_filename: The full path of the file that contains concerned symbol's daily stock prices
#   begin_year: The year from which to calculate returns
#
# Outputs:
#   A pandas series that contains the annual returns
#
# -------------------------------------------------------------------------------------------------
def calc_returns(prices_filename, begin_year):
    if not os.path.exists(filename): 
        return(None)

    stock_price = pd.read_csv(filename, index_col=0, parse_dates=True)

    if stock_price.empty or stock_price.index.name != 'Date':   # Check for errors   
        return(None)

    if not begin_year == None:
        stock_price = stock_price.loc[stock_price.index > pd.to_datetime(args.begin_year)]
        
    stock_price_monthly = stock_price['Close'].resample('M').last()
    
    if stock_price_monthly.empty:  # Make sure it isn't empty after resampling
        return(None)

    returns_dfs = stock_price_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
    if returns_dfs.empty:
        return(None)

    returns_dfs.dropna(inplace=True)
    return returns_dfs


# Parse command line arguments
msg = "Generates correlation matrix and risk-return tables on annual returns of SP500 stocks"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-b', '--begin_year', help='Year from which to consider data. If not supplied, oldest available year will be used')

args = parser.parse_args()

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Get a list of symbols to calculate covariances for
sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
sublist = sp500_list.loc[sp500_list['download_status'] == 'done']
symbols = list(sublist['Symbol'].values)
sectors = list(sublist['GICS Sector'].values)

corr_df = pd.DataFrame(columns=symbols, index=symbols])
risk_return = pd.DataFrame(columns=['sector', 'mean annual return', 'std annual return'], index=symbols)

rcount = 0
for rsymbol, rsector in tqdm(zip(symbols, sectors), desc='row progress'): # Iterating over row symbols
    filename = consolidated_prices_folder + '/' + rsymbol + '.csv'
    rreturns_dfs = calc_returns(filename, args.begin_year)
    
    for csymbol in tqdm(symbols, desc = 'col progress'): # Iterating over column symbols
        filename = consolidated_prices_folder + '/' + rsymbol + '.csv'
        creturns_dfs = calc_returns(filename, args.begin_year)
        
        # Calculate risk-return table
        if rcount == 0: # If this is the first row calculate risk table. Otherwise it would have already been calculated - so skip
            creturns = creturns_dfs.values   
            if creturns.size == 0:
                continue
            mean_ret = np.mean(creturns)
            std_ret = np.std(creturns) 
            if std_ret == 0:    # This could happen if there are two few samples in returns
                continue     

            risk_return.loc[rsymbol] = {'sector': rsector, 'mean annual return':mean_ret, 'std annual return':std_ret}
            
        # Calculate covariances
        if csymbol == rsymbol:  # Correlation coefficent of anything with itself is 1
            corr_df.loc[rsymbol, csymbol] = 1 
            continue

        if not math.isnan(corr_df.loc[rsymbol, csymbol]):   # If there is already a value present, it means an entry was made when 
            continue                                        # correlation coefficient was calculated for location csymbol, rsymbol

        corr_df.loc[rsymbol, csymbol] = rreturns_dfs.corr(creturns_dfs)
        corr_df.loc[csymbol, rsymbol] = corr_df.loc[rsymbol, csymbol] # Because correlation matrix is symmetric

    if rcount == 0:
        

