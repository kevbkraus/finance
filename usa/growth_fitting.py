# growth_fitting.py -----------------------------------------------------------------------------------------
#   Examines how investors behave when revenue growth and earnings growth are found to be above or below
# their expectations
# -----------------------------------------------------------------------------------------------------------

# Procedure
#   * Consider only companies that have a steady growth (slow, medium or fast, but no cyclicals, turn arounds)

import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import sklearn.metrics as metrics
import matplotlib.pyplot as plt
from datetime import datetime

import os
import sys
import argparse
from tqdm import tqdm, trange

# Parse command line arguments
msg = "Finds if investors respond positively when growth exceeds expectations and negatively when growth is below expectations"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-s', '--sector', help='GICS sector exactly as given in https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
parser.add_argument('-b', '--begin_year', help='Year from which to consider data. If not supplied, oldest available year will be used')

args = parser.parse_args()
if args.sector:
    sector = args.sector
else:
    sector = 'all'

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
if sector != 'all':
    sublist = sp500_list[(sp500_list['GICS Sector'] == sector) & (sp500_list['download_status'] == 'done')]
else:
    sublist = sp500_list.loc[sp500_list['download_status'] == 'done']

growth_price = pd.DataFrame(columns=['symbol', 'sector', 'revenue growth mismatch', 'earnings growth mismatch', 'price change', 'relative price change'])

filename = consolidated_prices_folder + '/' + 'sp500' + '.csv'
sp500 = pd.read_csv(filename, index_col=0, parse_dates=True) # S&P500 data is required for calculating beta for all stocks
sp500_monthly = sp500['Close'].resample('M').mean()
sp500_returns_dfs = sp500_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
count = 0
for i in tqdm(range(0,200), desc='Symbols processed:'): # We can select how many companies to consider for each run of this program. 
    symbol_idx = np.random.randint(0, len(sublist))
    symbol = sublist.iloc[symbol_idx].Symbol # Choose a random security
    sector = (sublist.iloc[symbol_idx])['GICS Sector']

    # Make sure it is indeed a growth company
    inc_stmt_filename = consolidated_prices_folder + '/income_statements/' + symbol + '_annual.csv'
    try:
        inc_stmt_annual = pd.read_csv(inc_stmt_filename, parse_dates=True) # Take income statement data if it has already been downloaded
    except Exception as e:        
        #print("Error while trying to open income statement for ", symbol, ". Error: ", e)
        continue

    if inc_stmt_annual.shape[0] < 5:
        print(symbol, ' does not have a long enough history')
        continue
 
    # Income statment typically has recent data first. But we want oldest data first
    inc_stmt_annual = inc_stmt_annual.reindex(index=inc_stmt_annual.index[::-1])
    inc_stmt_annual.reset_index(inplace=True)

    # Calculate growth figures for accepting/rejecting stock in question for further analysis
    avg_revenue_growth = np.nanmean(inc_stmt_annual['totalRevenue'].pct_change(periods=1).values)
    avg_earnings_growth = np.nanmean(inc_stmt_annual['netIncome'].pct_change(periods=1).values)
    
    if avg_revenue_growth < 0 or avg_earnings_growth < 0: # Probably a cyclical stock or declining stock
        #print(symbol, ' is not a growth company. Skipping')
        continue 

    # Get the average stock price of the concerned security in the month following 
    try:    
        stock_price = pd.read_csv(consolidated_prices_folder + '/' + symbol + '.csv', index_col=0, parse_dates=True)
    except Exception as e:
        print("Error while trying to open stock data for ", symbol, ". Error: ", e)
        continue
    
    stock_price_monthly = stock_price['Close'].resample('M').mean()
    returns_dfs = stock_price_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
    
    # Starting from 3rd year in 
    for idx in inc_stmt_annual.index:
        if idx<2:       # Linear regression requires at least two entries
            continue
       
        x = np.arange(0,idx).reshape(-1,1) # Regress revenue
        y = inc_stmt_annual.loc[0:idx-1, 'totalRevenue'].values
        model1 = LinearRegression()
        model1.fit(x,y)
        predicted_revenue = model1.predict(np.array(idx).reshape(1,-1))[0]
        #revenue_growth_mismatch = (inc_stmt_annual.loc[idx, 'totalRevenue'] - predicted_revenue)/predicted_revenue
        revenue_growth_mismatch = (inc_stmt_annual.loc[idx, 'totalRevenue'] - inc_stmt_annual.loc[idx-1, 'totalRevenue'])/inc_stmt_annual.loc[idx-1, 'totalRevenue']

        x = np.arange(0,idx).reshape(-1,1) # Regress earnings 
        y = inc_stmt_annual.loc[0:idx-1, 'netIncome'].values
        model2 = LinearRegression()
        model2.fit(x,y)
        predicted_earnings = model2.predict(np.array(idx).reshape(1,-1))[0] 
        #earnings_growth_mismatch = (inc_stmt_annual.loc[idx, 'netIncome'] - predicted_earnings)/predicted_earnings 
        earnings_growth_mismatch = (inc_stmt_annual.loc[idx, 'netIncome'] - inc_stmt_annual.loc[idx-1, 'netIncome'])/inc_stmt_annual.loc[idx-1, 'netIncome'] 
        
        stock_price_change = returns_dfs[returns_dfs.index > datetime.strptime(inc_stmt_annual.iloc[idx].fiscalDateEnding, '%Y-%m-%d')].iloc[0]
        index_change = sp500_returns_dfs[sp500_returns_dfs.index > datetime.strptime(inc_stmt_annual.iloc[idx].fiscalDateEnding, '%Y-%m-%d')].iloc[0]

        growth_price = growth_price.append({'symbol':symbol, 'sector':sector, 'revenue growth mismatch':revenue_growth_mismatch, 
                                            'earnings growth mismatch':earnings_growth_mismatch, 'price change':stock_price_change,
                                            'relative price change': (stock_price_change - index_change)}, ignore_index=True)
    count = count+1

# Visualisation
print('Symbols processed: ', count)
print(growth_price.to_markdown())

indices = (growth_price['earnings growth mismatch'] > growth_price['earnings growth mismatch'].mean()-growth_price['earnings growth mismatch'].std()) &\
          (growth_price['earnings growth mismatch'] < growth_price['earnings growth mismatch'].mean()+growth_price['earnings growth mismatch'].std())

fig1, ax1 = plt.subplots()
fig1.suptitle('Stock price change')
ax1.scatter(growth_price.loc[indices, 'revenue growth mismatch'], growth_price.loc[indices, 'price change'], color = 'blue', label = 'revenue')
ax1.scatter(growth_price.loc[indices, 'earnings growth mismatch'], growth_price.loc[indices, 'price change'], color = 'red', label = 'earnings')
ax1.legend()
  
fig2, ax2 = plt.subplots()
fig2.suptitle('Stock price change relative to index change')
ax2.scatter(growth_price.loc[indices, 'revenue growth mismatch'], growth_price.loc[indices, 'relative price change'], color = 'blue', label = 'revenue')
ax2.scatter(growth_price.loc[indices, 'earnings growth mismatch'], growth_price.loc[indices, 'relative price change'], color = 'red', label = 'earnings')
ax2.legend()

plt.show()


     
          
