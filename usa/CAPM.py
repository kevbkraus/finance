# CAPM.py -----------------------------------------------------------------------------------------
#   Examines CAPM in practice. Categorizes stocks in S&P500 according to their performances as 
# compared to CAPM prediction
#
# TODO: standard deviation or returns seems to be a better indicator of mean return with a lin reg
# r2 of 0.62, whereas beta seems to be a much poorer fit, with r2 = 0.22! This goes agains CAPM. Why?
# -------------------------------------------------------------------------------------------------

import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import sklearn.metrics as metrics
import matplotlib.pyplot as plt
import seaborn as sns

import os
import sys
import errno
from tqdm import tqdm, trange
import argparse

# Parse command line arguments
msg = "Examines CAPM in practice. Uses all SP500 stocks or stocks in a particular sector as supplied by the optional argument"
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

# Calculate stats
symbols = sublist['Symbol']
sectors = sublist['GICS Sector']
count = 0
risk_return = pd.DataFrame(columns=['symbol', 'sector', 'mean annual return', 'std annual return', 'beta'])

filename = consolidated_prices_folder + '/' + 'sp500' + '.csv'
sp500 = pd.read_csv(filename, index_col=0, parse_dates=True) # S&P500 data is required for calculating beta for all stocks
sp500_monthly = sp500['Close'].resample('M').last()
sp500_returns_dfs = sp500_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
sp500_returns_dfs.name = 'sp500'
for symbol, isector in tqdm(zip(symbols,sectors), desc='Symbols processed'):
    filename = consolidated_prices_folder + '/' + symbol + '.csv'
    try:    
        stock_price = pd.read_csv(filename, index_col=0, parse_dates=True)
    except Exception as e:
        print("Error while trying to open stock data for ", symbol, " Error: ", e)
        continue

    # Error checks
    if stock_price.empty:   # Empty csv file. Skip to next one
        continue

    if stock_price.index.name != 'Date':    # Otherwise following code would throw error and halt
        continue

    # Main code starts here
    if args.begin_year:
        stock_price = stock_price.loc[stock_price.index > pd.to_datetime(args.begin_year)]
        
    stock_price_monthly = stock_price['Close'].resample('M').last()
    if stock_price_monthly.empty:
        continue 

    returns_dfs = stock_price_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
    if returns_dfs.empty:
        continue

    returns_dfs.name = 'stock'
    new_df = pd.DataFrame(sp500_returns_dfs)
    new_df = new_df.join(returns_dfs)
    new_df.dropna(inplace=True)
    if new_df.empty:
        continue   
 
    stacked_mat = np.stack((new_df['stock'].values[1:], new_df['sp500'].values[1:]), axis=0)
    if stacked_mat.size == 0:
        continue
    
    cov_mat = np.cov(stacked_mat)
    beta = cov_mat[0,1]/cov_mat[1,1]

    mean_ret = np.mean(new_df['stock'].values)
    std_ret = np.std(new_df['stock'].values)
    if std_ret == 0:
        # print('Error: Standard deviation is 0. Symbol: ', symbol)
        continue     

    risk_return = risk_return.append({'symbol':symbol, 'sector': isector, 'mean annual return':mean_ret, 'std annual return':std_ret, 'beta':beta}, ignore_index=True)

    count = count+1

if not args.sector:
    risk_return.to_csv(consolidated_prices_folder + '/' + 'risk_return' + '.csv')

risk_return['return per risk'] = risk_return['mean annual return']/risk_return['beta']

# Eliminate outliers
left_q = risk_return[ 'return per risk'].quantile(0.25)
right_q = risk_return[ 'return per risk'].quantile(0.75)
candidate_iqr = right_q-left_q
regression_candidates = (risk_return['return per risk'] > (left_q-2.5*candidate_iqr)) & (risk_return['return per risk'] < (right_q+2.5*candidate_iqr))

# Run regression
x = risk_return.loc[regression_candidates, 'beta'].values.reshape((-1,1))
#x = risk_return['std annual return'].values.reshape((-1,1))
y = risk_return.loc[regression_candidates, 'mean annual return'].values
model = LinearRegression()
model.fit(x,y)
p = model.predict(x)


# Visualization and information display
median_df = risk_return.groupby(['sector']).median()
print(median_df.to_markdown())

fig1,ax1 = plt.subplots()
fig1.suptitle('Risk Vs. Return. Sector: ' + sector)
ax1.scatter(x, y, color='black')
ax1.plot(x, p, color='blue', linewidth=3)
ax1.set_xlabel('stock beta')
ax1.set_ylabel('expected annual return')

lrfit_details = "r-squared: %.2f, \nmse: %.4f, \n\nMarket excess return: %.2f, \nRisk free return: %.2f"\
                              %(metrics.r2_score(y,p),\
                                metrics.mean_squared_error(y,p),\
                                model.coef_,\
                                model.intercept_)

plt.text(x = 0.1, y = 0.9, s = lrfit_details, transform=ax1.transAxes,  
            horizontalalignment = "left", verticalalignment = "top", fontsize = 12) 
  

if not args.sector:
    sns.catplot(y='sector', x='return per risk', data=risk_return, kind='box', orient='h')
    sns.catplot(y='sector', x='beta', data=risk_return, kind='box', orient='h')

plt.show()
