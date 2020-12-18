
# hyp_test.py -------------------------------------------------------------------------------------
#   Performs hypothesis testing for a number of investment related hypotheses using data of SP500
# companies
# -------------------------------------------------------------------------------------------------

import requests
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
msg = "Performs hypothesis testing for a number of investment related hypotheses using data of SP500 companies"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('-s', '--sector', help="GICS sector exactly as given in Wikipedia - List_of S&P 500 companies")
parser.add_argument('-r', '--sample_size', help='Sample size. If not supplied, all pertinent stocks will be taken into consideration', type=int)
help_text = """Forcefully update non-price data (Ex. net income). If not supplied, preexising (possibly outdated)
               data will be used when available """ 
parser.add_argument('-f', '--update_data', help=help_text)
parser.add_argument('-b', '--begin_year', help='Year from which to consider data. If not supplied, oldest available year will be used')
help_text = """ (Hypothesis number) Hypothesis
                (1) PE ratio vs. net margin
                (2) Price vs. EBITDA
                (3) Return per risk vs. percentage held by instituitional investors
                (4) Best Return per risk stocks vs. SP500 """
parser.add_argument('hyp_num', help=help_text, type=int)

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
FMP_URL = "https://financialmodelingprep.com/api/v3"
FMP_KEY = os.environ.get('FMP_API_KEY')

sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')

args = parser.parse_args()

print(str(sys.argv))

if args.sector:                                 # This block of code is for debugging purposes
    print('Sector: ', args.sector)
if args.sample_size:
    print('Sample size: ', args.sample_size)
if args.update_data:
    print('Update Data: Yes')
if args.begin_year:
    print('Begin year: ', args.begin_year)
print('Hypothesis number: ', args.hyp_num) 

if args.sector:
    sublist = sp500_list[sp500_list['GICS Sector']==args.sector]
    sector = args.sector
else:
    sublist = sp500_list
    sector = args.sector

if args.sample_size:
    sublist = sublist.sample(args.sample_size)
    

# Main Code starts here:
if args.hyp_num == 1:
    print(' -----------------------------------------------------------------------------------------')
    print('                            PE ratio vs. Net margin                                       ')
    print(' -----------------------------------------------------------------------------------------')
    xy_df = pd.DataFrame(columns=['symbol', 'date', 'PE', 'net margin'])
    for symbol in tqdm(sublist['Symbol'].values, desc='Symbols processed:'):
        inc_stmt_filename = consolidated_prices_folder + '/annual_income_statements/' + symbol + '.csv'
        if args.update_data or (not os.path.exists(inc_stmt_filename)): # Get income statements from the net
            URL_SUFFIX = '/income-statement/' + symbol
            query_params = {'limit': 120, 'apikey': FMP_KEY}
            response = (requests.get(FMP_URL+URL_SUFFIX, params=query_params)).json()
            if not response: 
                print('Empty response received for ', symbol)
                continue
             
            inc_stmt_annual = pd.DataFrame(response)
            inc_stmt_annual['date'] = pd.to_datetime(inc_stmt_annual['date']).dt.date
            inc_stmt_annual.set_index('date', inplace=True)
            inc_stmt_annual.to_csv(inc_stmt_filename)
        else: 
            inc_stmt_annual = pd.read_csv(inc_stmt_filename, index_col=0, parse_dates=True) # Take income statement data if it has already been downloaded
        
        if args.begin_year:
            inc_stmt_annual = inc_stmt_annual.loc[inc_stmt_annual.index > pd.to_datetime(args.begin_year)]
        
        prices_filename = consolidated_prices_folder + '/' + symbol + '.csv'
        prices = pd.read_csv(prices_filename, index_col=0, parse_dates=True)
        prices_yearly = prices['Close'].resample('Y').mean()                    # Calculate PE ratios

        idx = list(map(lambda x: prices_yearly.index.get_loc(str(x), method='nearest'), inc_stmt_annual.index.values)) # Because dates don't match exactly between
                                                                                                                  # price dataframe and income statement data
                                                                                                                  # we have to find the nearest dates
        samples_df = pd.DataFrame({'symbol': symbol, 'date': inc_stmt_annual.index.values,
                                   'PE':prices_yearly.iloc[idx].values/inc_stmt_annual['eps'].values, 
                                   'net margin':inc_stmt_annual['netIncomeRatio'].values})
        xy_df = xy_df.append(samples_df, ignore_index=True)

    x = xy_df['net margin'].values.reshape((-1,1))
    y = xy_df['PE'].values
    model = LinearRegression()
    model.fit(x,y)
    p = model.predict(x)
    
    # Visualisation
    fig1,ax1 = plt.subplots()
    fig1.suptitle('Sector: ' + sector)
    ax1.scatter(x, y, color='black')
    ax1.plot(x, p, color='blue', linewidth=3)
    ax1.set_xlabel('Net margin (no unit)')
    ax1.set_ylabel('PE (no unit)')
    
    lrfit_details = "r-squared: %.2f, \nmse: %.4f, \n\nbeta: %.2f, \nalpha: %.2f"\
                                  %(metrics.r2_score(y,p),\
                                    metrics.mean_squared_error(y,p),\
                                    model.coef_,\
                                    model.intercept_)
    
    plt.text(x = 0.1, y = 0.9, s = lrfit_details, transform=ax1.transAxes,  
                horizontalalignment = "left", verticalalignment = "top", fontsize = 12)   
    plt.show()
        
elif args.hyp_num == 2:
    print(' -----------------------------------------------------------------------------------------')
    print('Price vs. EBITDA')
    print(' -----------------------------------------------------------------------------------------')
elif args.hyp_num == 3:
    print(' -----------------------------------------------------------------------------------------')
    print('Price vs. Net margin')
    print(' -----------------------------------------------------------------------------------------')
elif args.hyp_num == 4:
    print(' -----------------------------------------------------------------------------------------')
    print('Price vs. Net margin')
    print(' -----------------------------------------------------------------------------------------')
else:
    print("Entry error: Wrong hypothesis number")
 
