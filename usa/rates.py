# ----------------------------------------------------------------------------------------
# rates.py
#   Retrieves inflation rates, interest rates, returns rates of popular debt and equity
# benchmarks in the United States. All rates will be effective annual rates
#
# ----------------------------------------------------------------------------------------
import quandl
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import seaborn as sns

from datetime import date
from datetime import datetime

import os

# Set parameters
QUANDL_KEY = os.environ.get('QUANDL_API_KEY')
start = datetime(1990, 1, 31)
end = date.today()

# Get all the required data from the web
inflation = web.DataReader('RATEINF/INFLATION_USA', 'quandl', start, end, api_key = QUANDL_KEY)
mortgage_30Y = web.DataReader('FMAC/30US', 'quandl', start, end, api_key = QUANDL_KEY)
mortgage_5_1 = web.DataReader('FMAC/5US', 'quandl', start, end, api_key = QUANDL_KEY)
tnote_10Y = web.DataReader('FRED/WGS10YR', 'quandl', start, end, api_key = QUANDL_KEY) # This is 10-year t-note YTM

SP500 = web.DataReader(['sp500'], 'fred', start, end) # This is S&P 500 price values
SP500_monthly = SP500['sp500'].resample('M').last()
SP500_ret = pd.DataFrame(SP500_monthly.pct_change(periods = 12)*100) # Calculate annual returns at a granularity of 1 month

# Massage the data as required
mortgage_30Y['EAR'] = ((1 + mortgage_30Y.Value/(100*12))**12 - 1)*100
mortgage_5_1['EAR'] = ((1 + mortgage_5_1.Value/(100*12))**12 - 1)*100

# Adjusting for inflation: Convert all rates to monthly, add 1 to them and divide by (1+inflation)
mortgage_30Y_monthly = pd.DataFrame(mortgage_30Y['EAR'].resample('M').mean())
mortgage_5_1_monthly = pd.DataFrame(mortgage_5_1['EAR'].resample('M').mean())
tnote_10Y_monthly = tnote_10Y.resample('M').mean()

inflation = inflation.rename(columns = {'Value':'inflation'}) # So that, when we merge, we don't have a weird column named 'Value'
SP500_ret = SP500_ret.rename_axis('Date')
mortgage_30Y_monthly = pd.merge(mortgage_30Y_monthly, inflation, on = 'Date')
mortgage_5_1_monthly = pd.merge(mortgage_5_1_monthly, inflation, on = 'Date')
tnote_10Y_monthly = pd.merge(tnote_10Y_monthly, inflation, on = 'Date')
SP500_ret = pd.merge(SP500_ret, inflation, on = 'Date')

mortgage_30Y_monthly['infl_adj_EAR'] = ( ((mortgage_30Y_monthly['EAR']/100)+1)/((mortgage_30Y_monthly['inflation']/100)+1) - 1 )*100
mortgage_5_1_monthly['infl_adj_EAR'] = ( ((mortgage_5_1_monthly['EAR']/100)+1)/((mortgage_5_1_monthly['inflation']/100)+1) - 1 )*100
tnote_10Y_monthly['infl_adj_yield'] = ( ((tnote_10Y_monthly['Value']/100)+1)/((tnote_10Y_monthly['inflation']/100)+1) - 1 )*100
SP500_ret['infl_adj_EAR'] = ( ((SP500_ret['sp500']/100)+1)/((SP500_ret['inflation']/100)+1) - 1 )*100

# Visualization
sns.set_style('white')

fig = plt.figure(1)

ax1 = fig.add_subplot(221)
ax1.set_title('US Debt Returns $\it{nominal}$')
ax1.set_xlabel('date')
ax1.set_ylabel('returns (%)')
ax1.plot(inflation['inflation'], label = 'Inflation')
ax1.plot(tnote_10Y['Value'], label = 'Treasury note 10 year')
ax1.plot(mortgage_30Y.EAR, label = 'Fixed mortgage 30 year')
ax1.plot(mortgage_5_1.EAR, label = 'Adjustable mortgage 5/1')
ax1.grid(True)
ax1.legend()

ax2 = fig.add_subplot(222)
ax2.set_title('US Stock Returns $\it{nominal}$')
ax2.set_xlabel('date')
ax2.set_ylabel('returns (%)')
ax2.plot(tnote_10Y, label = 'Treasury note 10 year')
ax2.plot(SP500_ret['sp500'], label = 'S&P500')
ax2.grid(True)
ax2.legend()

ax3 = fig.add_subplot(223)
ax3.set_title('US Debt Returns $\it{real}$')
ax3.set_xlabel('date')
ax3.set_ylabel('returns (%)')
ax3.plot(tnote_10Y_monthly['infl_adj_yield'], label = 'Treasury note 10 year')
ax3.plot(mortgage_30Y_monthly['infl_adj_EAR'], label = 'Fixed mortgage 30 year')
ax3.plot(mortgage_5_1_monthly['infl_adj_EAR'], label = 'Adjustable mortgage 5/1')
ax3.grid(True)
ax3.legend()

ax4 = fig.add_subplot(224)
ax4.set_title('US Stock Returns $\it{real}$')
ax4.set_xlabel('date')
ax4.set_ylabel('returns (%)')
ax4.plot(tnote_10Y_monthly['infl_adj_yield'], label = 'Treasury note 10 year')
ax4.plot(SP500_ret['infl_adj_EAR'], label = 'S&P500')
ax4.grid(True)
ax4.legend()

plt.show()
