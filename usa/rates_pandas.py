# ---------------------------------------------------------------------------------------
# rates_pandas.py
#   (This is the version of rates.py that uses pandas plotting) 
#   Retrieves inflation rates, interest rates, returns rates of popular debt and equity
# benchmarks in the United States. All rates will be effective annual rates
#
# ----------------------------------------------------------------------------------------
import quandl
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import date, datetime

import os

# Functions
# ---------------------------------------------------------
# infl_adj
#   Adjusts an interest rate for inflation - ie., converts
# nominal rates to real rates.
#
# INPUTS 
# df:   The dataframe that contains the inflation rates and
#       the nominal rates that need to be adjusted
# col:  The name of the column that contains the nominal 
#       rates to be adjusted 
#
# OUTPUT
# real_rates: The real rates as a pandas series
# 
# Note: 
# 1.Input rates must be percentage figures. 
# 2.Output rates will be in percentage figures as well.
# 3.It is assumed that there is a column in the input
#   data frame called 'inflation'
#----------------------------------------------------------
def infl_adj(df, col):
    real_rates = ( ( (1 + df[col]/100) / (1 + df['inflation']/100) ) - 1 ) * 100
    return real_rates 

# Set parameters
QUANDL_KEY = os.environ.get('QUANDL_API_KEY')
start = datetime(1990, 1, 31)
end = date.today()
start_str = datetime.strftime(start, format='%Y-%m-%d')
end_str = datetime.strftime(end, format='%Y-%m-%d')

# Get all the required data from the web
inflation = web.DataReader('RATEINF/INFLATION_USA', 'quandl', start, end, api_key = QUANDL_KEY)
mortgage_30Y = web.DataReader('FMAC/30US', 'quandl', start, end, api_key = QUANDL_KEY)
mortgage_5_1 = web.DataReader('FMAC/5US', 'quandl', start, end, api_key = QUANDL_KEY)
tnote_10Y = web.DataReader('FRED/WGS10YR', 'quandl', start, end, api_key = QUANDL_KEY) # This is 10-year t-note YTM

CBond = web.DataReader('ML/USEY', 'quandl', start, end, api_key = QUANDL_KEY) 
A = web.DataReader('ML/AEY', 'quandl', start, end, api_key = QUANDL_KEY)
BBB = web.DataReader('ML/BBBEY', 'quandl', start, end, api_key = QUANDL_KEY)

SP500 = pd.DataFrame((yf.download('^GSPC', start = start_str, end = end_str, group_by='ticker')).Close)
DJI = pd.DataFrame((yf.download('^DJI', start = start_str, end = end_str, group_by='ticker')).Close)
nasdaq = pd.DataFrame((yf.download('^IXIC', start = start_str, end = end_str, group_by='ticker')).Close)

# -------------------PREPROCESSING DATA ------------------------------------------------------------------------
# Convert all data to monthly granularity because we need to inflation adjust them and inflation data is monthly
mortgage_30Y_monthly = mortgage_30Y.resample('M').mean()
mortgage_5_1_monthly = mortgage_5_1.resample('M').mean()
tnote_10Y_monthly = tnote_10Y.resample('M').mean()

CBond_monthly = CBond.resample('M').mean()
A_monthly = A.resample('M').mean()
BBB_monthly = BBB.resample('M').mean()

SP500_monthly = pd.DataFrame(SP500['Close'].resample('M').last())
DJI_monthly = pd.DataFrame(DJI['Close'].resample('M').last())
nasdaq_monthly = pd.DataFrame(nasdaq['Close'].resample('M').last())

# Change meaningless column names
inflation = inflation.rename(columns = {'Value':'inflation'}) 
mortgage_30Y_monthly = mortgage_30Y_monthly.rename(columns = {'Value':'mort_30Y_APR'})
mortgage_5_1_monthly = mortgage_5_1_monthly.rename(columns = {'Value':'mort_5_1_APR'})
tnote_10Y_monthly = tnote_10Y_monthly.rename(columns = {'Value':'T-note 10 year'})

CBond_monthly = CBond_monthly.rename(columns = {'BAMLC0A0CMEY' : 'US Bond'})
A_monthly = A_monthly.rename(columns = {'BAMLC0A3CAEY' : 'A'})
BBB_monthly = BBB_monthly.rename(columns = {'BAMLC0A4CBBBEY' : 'BBB'})

SP500_monthly = SP500_monthly.rename(columns = {'Close':'SP500_value'})
DJI_monthly = DJI_monthly.rename(columns = {'Close':'DJI_value'})
nasdaq_monthly = nasdaq_monthly.rename(columns = {'Close':'nasdaq_value'})

# Make all index names as 'Date' because we need to merge this with inflation data and inflation data index name is 'Date'
CBond = CBond.rename_axis(index = {'DATE':'Date'})
A = A.rename_axis(index = {'DATE':'Date'})
BBB = BBB.rename_axis(index = {'DATE':'Date'})

# Calculate annual rates
mortgage_30Y_monthly['mortgage 30 year'] = ((1 + mortgage_30Y_monthly['mort_30Y_APR']/(100*12))**12 - 1)*100 # Convert APR to EAR
mortgage_5_1_monthly['adjustable mortgage (5-1)'] = ((1 + mortgage_5_1_monthly['mort_5_1_APR']/(100*12))**12 - 1)*100

SP500_monthly['SP500'] = SP500_monthly['SP500_value'].pct_change(periods = 12)*100 # Calculate annual returns at a granularity of 1 month
DJI_monthly['DJI'] = DJI_monthly['DJI_value'].pct_change(periods = 12)*100 # Calculate annual returns at a granularity of 1 month
nasdaq_monthly['nasdaq'] = nasdaq_monthly['nasdaq_value'].pct_change(periods = 12)*100 # Calculate annual returns at a granularity of 1 month

# Merge all rates to create a super data frame
allrates = inflation.copy()
allrates = allrates.join(mortgage_30Y_monthly['mortgage 30 year'], how = 'left')
allrates = allrates.join(mortgage_5_1_monthly['adjustable mortgage (5-1)'], how = 'left')
allrates = allrates.join(tnote_10Y_monthly['T-note 10 year'], how = 'left')

allrates = allrates.join(CBond_monthly['US Bond'], how = 'left')
allrates = allrates.join(A_monthly['A'], how = 'left')
allrates = allrates.join(BBB_monthly['BBB'], how = 'left')

allrates = allrates.join(SP500_monthly['SP500'], how = 'left')
allrates = allrates.join(DJI_monthly['DJI'], how = 'left')
allrates = allrates.join(nasdaq_monthly['nasdaq'], how = 'left', sort = 'True')

# Adjusting nominal rates for inflation to get real rates
allrates['mortgage 30 year (real)'] = infl_adj(allrates, 'mortgage 30 year') 
allrates['adjustable mortgage (5-1) (real)'] = infl_adj(allrates, 'adjustable mortgage (5-1)') 
allrates['US Bond (real)'] = infl_adj(allrates, 'US Bond') 
allrates['A (real)'] = infl_adj(allrates, 'A') 
allrates['BBB (real)'] = infl_adj(allrates, 'BBB') 
allrates['SP500 (real)'] = infl_adj(allrates, 'SP500') 
allrates['DJI (real)'] = infl_adj(allrates, 'DJI') 
allrates['nasdaq (real)'] = infl_adj(allrates, 'nasdaq') 

# Visualization
allrates.plot(y = ['inflation', 'T-note 10 year'], kind = 'line', grid = True, title = 'Benchmark Returns (%)')
allrates.plot(y = ['mortgage 30 year (real)', 'adjustable mortgage (5-1) (real)'], kind = 'line', grid = True, title = 'Personal Debt Returns (%)')
allrates.plot(y = ['US Bond (real)', 'A (real)', 'BBB (real)'], kind = 'line', grid = True, title = 'Corporate Bond Returns (%)')
allrates.plot(y = ['SP500 (real)', 'DJI (real)', 'nasdaq (real)'], kind = 'line', grid = True, title = 'Stock Returns (%)')

plt.show()
