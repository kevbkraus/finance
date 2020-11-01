# ----------------------------------------------------------------------------------------
# rates.py
#   Retrieves inflation rates, interest rates, returns rates of popular debt and equity
# benchmarks in the United States. All rates will be effective annual rates
#
# ----------------------------------------------------------------------------------------
import quandl
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import date

## Initial parameter setting/configuration
#quandl.ApiConfig.api_key = 'Sr4WHFjsCYYDoG5yfVNh'
#today = date.today()
#today_dash = today.strftime('%Y-%m-%d')
#begin_date = '1990-01-31' 
#
## Get inflation rate
#inflation = quandl.get('RATEINF/INFLATION_USA', start_date = begin_date, end_date = today_dash)
#mortgage_30Y = quandl.get('FMAC/30US', start_date = begin_date, end_date = today_dash)
#mortgage_30Y['EAR'] = ((1 + mortgage_30Y.Value/(100*12))**12 - 1)*100
#mortgage_5_1 = quandl.get('FMAC/5US', start_date = begin_date, end_date = today_dash)
#mortgage_5_1['EAR'] = ((1 + mortgage_5_1.Value/(100*12))**12 - 1)*100
#t_note_10Y = quandl.get('FRED/WGS10YR', start_date = begin_date, end_date = today_dash) # 10 year t-note yield
#
## Visualisation
#sns.set_style('whitegrid') # Configure plot style
#
#fig, ax = plt.subplots()
#fig.suptitle('Rates (Annualized)', fontsize = 14)
#ax.plot(inflation, label = 'inflation')
#ax.plot(t_note_10Y, label = 'Treasury note 10 year')
#ax.plot(mortgage_30Y.EAR, label = 'Fixed mortgage 30 year')
#ax.plot(mortgage_5_1.EAR, label = 'Adjustable mortgage 5/1')
#
#ax.legend()
#plt.show()

# Same, but with pandas datareader
import pandas_datareader.data as web
from datetime import datetime

# Set parameters
QUANDL_KEY = 'Sr4WHFjsCYYDoG5yfVNh'
start = datetime(1990, 1, 31)
end = date.today()

# Get all the required data from the web
inflation = web.DataReader('RATEINF/INFLATION_USA', 'quandl', start, end, api_key = QUANDL_KEY)
mortgage_30Y = web.DataReader('FMAC/30US', 'quandl', start, end, api_key = QUANDL_KEY)
mortgage_5_1 = web.DataReader('FMAC/5US', 'quandl', start, end, api_key = QUANDL_KEY)
t_note_10Y = web.DataReader('FRED/WGS10YR', 'quandl', start, end, api_key = QUANDL_KEY) # This is 10-year t-note YTM

SP500 = web.DataReader(['sp500'], 'fred', start, end) # This is S&P 500 price values
SP500_monthly = SP500['sp500'].resample('M').last()
SP500_annual_ret = SP500_monthly.pct_change(periods = 12)*100 # Calculate annual returns at a granularity of 1 month

# Massage the data as required
mortgage_30Y['EAR'] = ((1 + mortgage_30Y.Value/(100*12))**12 - 1)*100
mortgage_5_1['EAR'] = ((1 + mortgage_5_1.Value/(100*12))**12 - 1)*100

# Visualization
fig = plt.figure(1)

ax1 = fig.add_subplot(211)
ax1.plot(inflation, label = 'Inflation')
ax1.plot(t_note_10Y, label = 'Treasury note 10 year')
ax1.plot(mortgage_30Y.EAR, label = 'Fixed mortgage 30 year')
ax1.plot(mortgage_5_1.EAR, label = 'Adjustable mortgage 5/1')
ax1.legend()

ax2 = fig.add_subplot(212)
ax2.plot(t_note_10Y, label = 'Treasury note 10 year')
ax2.plot(SP500_annual_ret, label = 'S&P500')
ax2.legend()

plt.show()
