# CAPM.py -----------------------------------------------------------------------------------------
#   Examines CAPM in practice. Categorizes stocks in S&P500 according to their performances as 
# compared to CAPM prediction
#
# -------------------------------------------------------------------------------------------------

import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import sklearn.metrics as metrics
import matplotlib.pyplot as plt

import os
import sys
import errno
from tqdm import tqdm, trange
import argparse

# Parse command line arguments
msg = "Examines CAPM in practice. Uses all SP500 stocks or stocks in a particular sector as supplied by the optional argument"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-s', '--sector', help='GICS sector exactly as given in https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

args = parser.parse_args()
if args.sector:
    sector = args.sector
else:
    sector = 'all'

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')
if sector != 'all':
    sublist = sp500_list.loc[(sp500_list['GICS Sector'] == sector) and (sp500_list['download_status'] == 'done')]
else:
    sublist = sp500_list.loc[sp500_list['download_status'] == 'done']

symbols = sublist['Symbol']
count = 0
risk_return = pd.DataFrame(columns=['symbol', 'mean annual return', 'std annual return'])
for symbol in tqdm(symbols, desc='Symbols processed'):
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
    stock_price_monthly = stock_price['Close'].resample('M').last()
    if stock_price_monthly.empty:
        continue 

    returns_dfs = stock_price_monthly.pct_change(periods=12)    # Compute annual returns at the granularity of 1 month
    if returns_dfs.empty:
        continue

    returns_dfs.dropna(inplace=True)
    returns = returns_dfs.values   
    if returns.size == 0:
        continue

    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    if std_ret == 0:
        # print('Error: Standard deviation is 0. Symbol: ', symbol)
        continue     

    risk_return = risk_return.append({'symbol':symbol, 'mean annual return':mean_ret, 'std annual return':std_ret}, ignore_index=True)

    count = count+1


risk_return.to_csv(consolidated_prices_folder + '/' + 'risk_return' + '.csv')
x = risk_return['std annual return'].values.reshape((-1,1))
y = risk_return['mean annual return'].values
model = LinearRegression()
model.fit(x,y)
p = model.predict(x)

# Visualization
fig1,ax1 = plt.subplots()
fig1.suptitle('Sector: ' + sector)
ax1.scatter(x, y, color='black')
ax1.plot(x, p, color='blue', linewidth=3)
ax1.set_xlabel('risk')
ax1.set_ylabel('return')

lrfit_details = "r-squared: %.2f, \nmse: %.4f, \n\nbeta: %.2f, \nalpha: %.2f"\
                              %(metrics.r2_score(y,p),\
                                metrics.mean_squared_error(y,p),\
                                model.coef_,\
                                model.intercept_)

plt.text(x = 0.1, y = 0.9, s = lrfit_details, transform=ax1.transAxes,  
            horizontalalignment = "left", verticalalignment = "top", fontsize = 12)   
plt.show()
