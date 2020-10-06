# single_security_analysis.py ---------------------------------------------------------------------------
# Description:
#   1. Examines the data for missing values and informs user if there are too many missing values 
#   2. Produces data and visuals for EDA of a given security
#   3. Compares the security with the market's risk, creates visuals pertaining to the same
#   4. Appends useful data resulting from all the above analysis to the raw data and stores the result
#      in a new csv file
# -------------------------------------------------------------------------------------------------------

# Libraries
import math
import numpy as np
import numpy.linalg as la
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

import calendar
import sys
import errno

# Default parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/india/NSE-EOD'

# Get input from user for the file that has NSE price data of the security in question
nse_symbol = input('Enter NSE symbol: ')
file_name = consolidated_prices_folder + '/' + nse_symbol + '.csv'
# Preprocessing
try:
    raw_data = pd.read_csv(file_name)
except Exception as e:
    print("Error while opening file: ", e)
    sys.exit(errno.EIO)

print(raw_data.head())  # Display few rows just so that user can see if there is anything unusual

old_colnames = list(raw_data.columns)   # Change column names to remove the annoying '<', '>'
new_colnames = [name[1:-1] for name in old_colnames]
raw_data.columns = new_colnames

refined_data = raw_data.sort_values(by='date')    # Sort data according to date and drop duplicates
refined_data.dropna(subset=['close'], inplace=True) # Drop rows with na values for stock closing price - 
refined_data.drop_duplicates(inplace=True)          # We use stock closing price for all returns calcs

dates = pd.to_datetime(refined_data['date'], format="%Y%m%d") # Extract year, month names and weekday names
years = [item.year for item in dates]                           # and add new columns for these in the refined
months = [item.month for item in dates]                        # data. This will be very useful later when we
weekdays = [item.weekday() for item in dates]                   # create plots
weekdays_name = [calendar.day_name[day] for day in weekdays]
months_name = [calendar.month_abbr[month] for month in months]

refined_data = refined_data.assign(year = years)           # Creating new columns that will be useful for EDA
refined_data = refined_data.assign(month = months_name)
refined_data = refined_data.assign(day = weekdays_name)

yeargroup = refined_data.groupby('year')    # This entire code handles data in yearly tranches
figure_id = 1
daily_outlier_df = pd.DataFrame()
for year,groupdata in yeargroup:
    dates = pd.to_datetime(groupdata['date'], format="%Y%m%d")
    totaldays = (max(dates) - min(dates)).days
    if len(dates) < (int(totaldays * (5/7)) - 15 - 5):  # If we have lesser day entries even after we account for
                                                        # weekends, 15 (typical) yearly holidays and 5 extra days
                                                        # a margin, then the user needs to be warned of the same             
        yn = input('Year '+str(year)+' has too many missing days. Continue? (y/n): ')
        if yn == 'n':
            printing("User halted code")
            sys.exit()

    prices = groupdata['close'].values  # Calculate daily returns
    prevday_prices = np.roll(prices, 1)     # Shift closing prices by 1 so we can divide prices by previous day prices
    prevday_prices[0] = prevday_prices[1]  # np.roll ends up rolling over last element to the first element - we don't 
                                            # - want that 
    discount_factors = prices/prevday_prices    
    dayfactors = np.array([x.days for x in dates.diff()])
    dayfactors[0] = 1   # To remove NaN. 
    normalised_discount_factors = np.power(discount_factors, 1/dayfactors)    # This is done so that, weekends and holidays
                                                                            # don't artificially show high returns
    daily_returns = normalised_discount_factors - 1 
    refined_data = refined_data.assign(returns = daily_returns)
    
    daily_outlier_indices = np.where(np.abs(stats.zscore(daily_returns)) > 2)    # We consider anything beyond +/- 2 sigma
    outlier_dates = np.datetime_as_string(dates.values[daily_outlier_indices], timezone='UTC', unit='h')
    outlier_dates_str = [item[0:-4] for item in outlier_dates]
    
    daily_outlier_df = daily_outlier_df.assign(returns = daily_returns[daily_outlier_indices])      # as outliers
    daily_outlier_df = daily_outlier_df.assign(dates = outlier_dates_str)

    # Description and visualisation
    print('\n -------------- Returns Summary ---------------')
    print(refined_data.returns.describe())
    print('\nOutliers:')
    print(daily_outlier_df)
    
    days_ordered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']  
    months_ordered = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    fig1 = plt.figure(figure_id)
    figure_id = figure_id + 1
    fig1.suptitle('Daily Returns', fontsize=16)
    ax1 = fig1.add_subplot(221)
    sns.histplot(x = 'returns', color = 'green', data = refined_data, kde = True, ax = ax1)
    plt.axvline(refined_data['returns'].mean(), 0,1, color = 'red')    
    
    ax2 = fig1.add_subplot(222)
    sns.boxplot(x = 'day', y = 'returns', order = days_ordered, data = refined_data, ax = ax2)

    ax3 = fig1.add_subplot(223)
    sns.boxplot(x = 'month', y = 'returns', order = months_ordered, data = refined_data, ax = ax3)

    plt.show() 


