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
        return pd.Series([], dtype = 'float64')

    stock_price = pd.read_csv(filename, index_col=0, parse_dates=True)

    if stock_price.empty or stock_price.index.name != 'Date':   # Check for errors   
        return pd.Series([], dtype = 'float64')

    if not begin_year == None:
        stock_price = stock_price.loc[stock_price.index > pd.to_datetime(args.begin_year)]
        
    stock_price_monthly = stock_price['Close'].resample('M').last()
    
    if stock_price_monthly.empty:  # Make sure it isn't empty after resampling
        return pd.Series([], dtype = 'float64')

    returns_dfs = stock_price_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
    if returns_dfs.empty:
        return pd.Series([], dtype = 'float64')

    returns_dfs.dropna(inplace=True)
    return returns_dfs


# Parse command line arguments
msg = "Generates correlation matrix and risk-return tables on annual returns of SP500 stocks"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-b', '--begin_year', help='Year from which to consider data. If not supplied, oldest available year will be used')

args = parser.parse_args()

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
if args.begin_year:
    risk_return_filename = consolidated_prices_folder + '/risk_return_' + args.begin_year + '.csv'
    corr_mat_filename = consolidated_prices_folder + '/corr_mat_' + args.begin_year + '.csv'
    corr_strength_filename = consolidated_prices_folder + '/corr_strength_' + args.begin_year + '.csv' 
else:
    risk_return_filename = consolidated_prices_folder + '/risk_return.csv'
    corr_mat_filename = consolidated_prices_folder + '/corr_mat.csv'
    corr_strength_filename = consolidated_prices_folder + '/corr_strength.csv' 

# Get a list of symbols to calculate covariances for
sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
sublist = sp500_list.loc[sp500_list['download_status'] == 'done']
symbols = list(sublist['Symbol'].values)
sectors = list(sublist['GICS Sector'].values)

corr_df = pd.DataFrame(columns=symbols, index=symbols)
corr_strength_df = pd.DataFrame(columns=symbols, index=symbols)
risk_return = pd.DataFrame(columns=['sector', 'mean annual return', 'std annual return', 'sample_count'], index=symbols)

rcount = 0
for rsymbol in tqdm(symbols, desc='row progress'): # Iterating over row symbols
    filename = consolidated_prices_folder + '/' + rsymbol + '.csv'
    rreturns_dfs = calc_returns(filename, args.begin_year)
    if rreturns_dfs.empty or rreturns_dfs.shape[0] < 36: # Make sure there aren't too few samples for computing correlation
        continue
    rreturns_dfs.rename(rsymbol, inplace=True)
 
    for csymbol, sector in zip(symbols, sectors): # Iterating over column symbols
        filename = consolidated_prices_folder + '/' + csymbol + '.csv'
        creturns_dfs = calc_returns(filename, args.begin_year)
        if creturns_dfs.empty or creturns_dfs.shape[0] < 36: # Make sure there aren't too few samples for computing correlation 
            continue
        creturns_dfs.rename(csymbol, inplace=True) 

        # Calculate risk-return table
        if rcount == 0: # If this is the first row calculate risk table. Otherwise it would have already been calculated - so skip
            mean_ret = np.mean(creturns_dfs.values)
            std_ret = np.std(creturns_dfs.values) 
            risk_return.loc[csymbol] = {'sector': sector, 'mean annual return':mean_ret, 'std annual return':std_ret, 'sample_count':creturns_dfs.shape[0]}
            
        # Calculate covariances
        if csymbol == rsymbol:  # Correlation coefficent of anything with itself is 1
            corr_df.loc[rsymbol, csymbol] = 1 
            continue

        if not math.isnan(corr_df.loc[rsymbol, csymbol]):   # If there is already a value present, it means an entry was made when 
            continue                                        # correlation coefficient was calculated for location csymbol, rsymbol

        temp_df = pd.concat([rreturns_dfs, creturns_dfs], axis=1) # This df is required just to drop na and calc strength of correlation
        temp_df.dropna(inplace=True)
        corr_result = (temp_df.corr()).loc[rsymbol, csymbol]
        corr_df.loc[rsymbol, csymbol] = corr_result  # store correlation and how many samples were used in determining it
        corr_df.loc[csymbol, rsymbol] = corr_df.loc[rsymbol, csymbol] # Because correlation matrix is symmetric
        corr_strength_df.loc[rsymbol, csymbol] = temp_df.shape[0]
        corr_strength_df.loc[csymbol, rsymbol] = corr_strength_df.loc[rsymbol, csymbol]  
    
    if rcount == 0:
        risk_return.to_csv(risk_return_filename)

    rcount = rcount + 1
    if rcount%20 == 0:  # Every 20 row symbols, save the results in a file so that all isn't lost if the programe unexpectedly terminates
        corr_df.to_csv(corr_mat_filename)
        corr_strength_df.to_csv(corr_strength_filename)

corr_df.to_csv(corr_mat_filename)   # At the very end of all iterations, save again


