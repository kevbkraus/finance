import math
import numpy as np
import pandas as pd
from pprint import pprint
import matplotlib.pyplot as plt

import os
import sys
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
    if not os.path.exists(prices_filename): 
        return pd.Series([], dtype = 'float64')

    stock_price = pd.read_csv(prices_filename, index_col=0, parse_dates=True)

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

def overlap_returns(symbol_a, symbol_b, sp500_list):
    stock_a_name = sp500_list[sp500_list['Symbol'] == symbol_a]['Security'].values[0]
    stock_a_sector = sp500_list[sp500_list['Symbol'] == symbol_a]['GICS Sector'].values[0]
    stock_b_name = sp500_list[sp500_list['Symbol'] == symbol_b]['Security'].values[0]
    stock_b_sector = sp500_list[sp500_list['Symbol'] == symbol_b]['GICS Sector'].values[0]
    title_str = 'Returns comparison between %s (%s) and %s (%s)' %(stock_a_name, stock_a_sector, stock_b_name, stock_b_sector) 
    
    # Calulate annual returns for both securities in question and combine them 
    areturns_dfs = calc_returns(consolidated_prices_folder + '/' + symbol_a + '.csv', None)
    #areturns_dfs = areturns_dfs - areturns_dfs.mean() 
    areturns_dfs.rename(symbol_a, inplace=True) 
    
    breturns_dfs = calc_returns(consolidated_prices_folder + '/' + symbol_b + '.csv', None)
    #breturns_dfs = breturns_dfs - breturns_dfs.mean() 
    breturns_dfs.rename(symbol_b, inplace=True) 
    
    temp_df = pd.concat([areturns_dfs, breturns_dfs], axis=1) # This df is required just to drop na and calc strength of correlation
    temp_df.dropna(inplace=True)
    
    temp_df.plot(y=[symbol_a, symbol_b], title=title_str, kind='line')


# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
risk_return_filename = consolidated_prices_folder + '/risk_return.csv'
corr_mat_filename = consolidated_prices_folder + '/corr_mat.csv'
corr_strength_filename = consolidated_prices_folder + '/corr_strength.csv' 
sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')

# Command line argument stuff
msg = "General purpose scratch pad"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-n', '--min_num_count', type=int, help='How many min correlation values to find. Default 10')
parser.add_argument('-c', '--compare', nargs=2, help='stock symbols to compare')
parser.add_argument('--sector_compare', nargs=2, help='Compare two GICS sectors')

args = parser.parse_args()
if args.compare:
    overlap_returns(args.compare[0], args.compare[1], sp500_list)
elif args.sector_compare: # Filter out only sectors supplied by the user
    sector_a_symbols = sp500_list[sp500_list['GICS Sector'] == args.sector_compare[0]]['Symbol'].values 
    sector_b_symbols = sp500_list[sp500_list['GICS Sector'] == args.sector_compare[1]]['Symbol'].values 
    corr_all_df = pd.read_csv(corr_mat_filename, index_col=0)
    corr_df = corr_all_df.loc[sector_a_symbols, sector_b_symbols]
    min_s = corr_df.min(skipna=True)
    min_s.rename('min', inplace=True)
    max_s = corr_df.max(skipna=True)
    max_s.rename('max', inplace=True)
    mean_s = corr_df.mean(skipna=True)
    mean_s.rename('mean', inplace=True)
    median_s = corr_df.median(skipna=True)
    median_s.rename('median', inplace=True)
    corr_sectors = pd.concat([min_s, max_s, mean_s, median_s], axis=1)
    print(' Sector correlation coefficient statistics:')
    pprint(corr_sectors)
else:
    if args.min_num_count:
        min_num_count = args.min_num_count
    else:
        min_num_count = 10
    
    corr_df = pd.read_csv(corr_mat_filename, index_col=0)
    
    # Efficient way to find stock pairs that give n min correlation coefficient values  
    min_s = corr_df.min(skipna=True)    # Results in a series that contains, as its index, the columns of corr_df and
                                        # its values as the min value in the corresponding column of corr_df
    min_s.sort_values(inplace=True)     # Sort in ascending order from min value to max value
    stock_tuples = list(map(lambda x: (corr_df.index[corr_df[min_s.index[x]] == min_s[x]][0], min_s.index[x]), range(0,2*min_num_count)))   # The reason - 
                                        # for doubling min_num_count is that after we drop duplicates, we may end up with min_num_count
    stock_tuples_unique = list()    # 
    temp_useless_obj = [stock_tuples_unique.append((a,b)) for (a,b) in stock_tuples if (b,a) not in stock_tuples_unique]
    print('List of stock tuples that have min correlation coefficients (smallest to largetst:')
    pprint(stock_tuples_unique[0:min_num_count])
    
    for i,combo in enumerate(stock_tuples_unique[0:min_num_count]):
        overlap_returns(combo[0], combo[1], sp500_list)

plt.show()
