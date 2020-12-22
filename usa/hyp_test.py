
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
parser.add_argument('-b', '--begin_year', help='Year from which to consider data. If not supplied, oldest available year will be used')
help_text = """ (Hypothesis number) Hypothesis
                (1) PE ratio vs. net margin
                (2) Price vs. Ebitda ratio
                (3) Return per risk vs. percentage held by instituitional investors
                (4) Best Return per risk stocks vs. SP500 """
parser.add_argument('hyp_num', help=help_text, type=int)

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
sp500_list = pd.read_csv(consolidated_prices_folder + '/download_log.csv')

args = parser.parse_args()

print(str(sys.argv))

if args.sector:
    sublist = sp500_list[sp500_list['GICS Sector']==args.sector]
    sector = args.sector
else:
    sublist = sp500_list
    sector = 'all' 

if args.sample_size:
    sublist = sublist.sample(args.sample_size)
    
# Main Code starts here:
if args.hyp_num == 1 or args.hyp_num == 2:
    if args.hyp_num == 1:
        print(' -----------------------------------------------------------------------------------------')
        print('                            PE ratio vs. Net margin                                       ')
        print(' -----------------------------------------------------------------------------------------')
    else:
        print(' -----------------------------------------------------------------------------------------')
        print('                            PE ratio vs. Ebitda margin                                    ')
        print(' -----------------------------------------------------------------------------------------')
    
    xy_df = pd.DataFrame(columns=['symbol', 'date', 'PE', 'margin'])
    processed_count = 0
    unprocessed_count = 0
    for symbol in tqdm(sublist['Symbol'].values, desc='Symbols processed:'):
        inc_stmt_filename = consolidated_prices_folder + '/income_statements/' + symbol + '_annual.csv'
        if not os.path.exists(inc_stmt_filename): 
            unprocessed_count = unprocessed_count + 1
            continue
             
        inc_stmt_annual = pd.read_csv(inc_stmt_filename, index_col=0, parse_dates=True) # Take income statement data if it has already been downloaded
        
        if args.begin_year:
            inc_stmt_annual = inc_stmt_annual.loc[inc_stmt_annual.index > pd.to_datetime(args.begin_year)]
        
        prices_filename = consolidated_prices_folder + '/' + symbol + '.csv'
        prices = pd.read_csv(prices_filename, index_col=0, parse_dates=True)
        prices_yearly = prices['Close'].resample('Y').mean()                    # Calculate PE ratios

        idx = list(map(lambda x: prices_yearly.index.get_loc(str(x), method='nearest'), inc_stmt_annual.index.values)) # Because dates don't match exactly between
                                                                                                                  # price dataframe and income statement data
        if args.hyp_num == 1:                                                                                                          # we have to find the nearest dates
            samples_df = pd.DataFrame({'symbol': symbol, 'date': inc_stmt_annual.index.values,
                                       'PE':prices_yearly.iloc[idx].values/inc_stmt_annual['eps'].values, 
                                       'margin':inc_stmt_annual['netIncomeRatio'].values})
        else:
            samples_df = pd.DataFrame({'symbol': symbol, 'date': inc_stmt_annual.index.values,
                                       'PE':prices_yearly.iloc[idx].values/inc_stmt_annual['eps'].values, 
                                       'margin':inc_stmt_annual['ebitdaratio'].values})
        xy_df = xy_df.append(samples_df, ignore_index=True)
        processed_count = processed_count + 1

    # Eliminate outliers
    PE_Q1 = xy_df['PE'].quantile(0.25)
    PE_Q3 = xy_df['PE'].quantile(0.75)
    marg_Q1 = xy_df['margin'].quantile(0.25)
    marg_Q3 = xy_df['margin'].quantile(0.75)
    xy_df = xy_df[(xy_df['PE'] > (PE_Q1 - 1.5*PE_IQR)) & (xy_df['PE'] < (PE_Q3 + 1.5*PE_IQR))]
    xy_df = xy_df[(xy_df['margin'] > (marg_Q1 - 1.5*marg_IQR)) & (xy_df['margin'] < (marg_Q3 + 1.5*marg_IQR))]
   
    # Linear regression 
    x = xy_df['margin'].values.reshape((-1,1))
    y = xy_df['PE'].values
    model = LinearRegression()
    model.fit(x,y)
    p = model.predict(x)
    
    # Visualisation and information display
    print('Processed symbols: ', processed_count)
    print('Unprocessed symbols: ', unprocessed_count)
    
    fig1,ax1 = plt.subplots()
    fig1.suptitle('Sector: ' + sector)
    ax1.scatter(x, y, color='black')
    ax1.plot(x, p, color='blue', linewidth=3)
    if args.hyp_num == 1:
        ax1.set_xlabel('Net margin (no unit)')
    else:
        ax1.set_xlabel('Ebitda margin (no unit)')

    ax1.set_ylabel('PE (no unit)')
    
    lrfit_details = "r-squared: %.2f, \nmse: %.4f, \n\nbeta: %.2f, \nalpha: %.2f"\
                                  %(metrics.r2_score(y,p),\
                                    metrics.mean_squared_error(y,p),\
                                    model.coef_,\
                                    model.intercept_)
    
    plt.text(x = 0.1, y = 0.9, s = lrfit_details, transform=ax1.transAxes,  
                horizontalalignment = "left", verticalalignment = "top", fontsize = 12)   
    plt.show()
        
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
 
