# ---------------------------------------------------------------------------------------
# rates.py
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
# Change meaningless column names
inflation = inflation.rename(columns = {'Value':'inflation'}) 
CBond = CBond.rename(columns = {'BAMLC0A0CMEY' : 'yield'})
A = A.rename(columns = {'BAMLC0A3CAEY' : 'yield'})
BBB = BBB.rename(columns = {'BAMLC0A4CBBBEY' : 'yield'})

# Make all index names as 'Date' because we need to merge this with inflation data and inflation data index name is 'Date'
CBond = CBond.rename_axis(index = {'DATE':'Date'})
A = A.rename_axis(index = {'DATE':'Date'})
BBB = BBB.rename_axis(index = {'DATE':'Date'})

# Convert all data to monthly granularity because we need to inflation adjust them and inflation data is monthly
mortgage_30Y_monthly = mortgage_30Y.resample('M').mean()
mortgage_5_1_monthly = mortgage_5_1.resample('M').mean()
tnote_10Y_monthly = tnote_10Y.resample('M').mean()

CBond_monthly = CBond.resample('M').mean()
A_monthly = A.resample('M').mean()
BBB_monthly = BBB.resample('M').mean()

SP500_monthly = SP500['Close'].resample('M').last()
DJI_monthly = DJI['Close'].resample('M').last()
nasdaq_monthly = nasdaq['Close'].resample('M').last()

mortgage_30Y_monthly['EAR'] = ((1 + mortgage_30Y_monthly.Value/(100*12))**12 - 1)*100 # Convert APR to EAR
mortgage_5_1_monthly['EAR'] = ((1 + mortgage_5_1_monthly.Value/(100*12))**12 - 1)*100

SP500_ret = pd.DataFrame(SP500_monthly.pct_change(periods = 12)*100) # Calculate annual returns at a granularity of 1 month
DJI_ret = pd.DataFrame(DJI_monthly.pct_change(periods = 12)*100) # Calculate annual returns at a granularity of 1 month
nasdaq_ret = pd.DataFrame(nasdaq_monthly.pct_change(periods = 12)*100) # Calculate annual returns at a granularity of 1 month

# Change column names to make senseSP500_ret = SP500_ret.rename(columns={'Close':'return'})
SP500_ret = SP500_ret.rename(columns={'Close':'return'})
DJI_ret = DJI_ret.rename(columns={'Close':'return'})
nasdaq_ret = nasdaq_ret.rename(columns={'Close':'return'})

# Adjusting for inflation: Convert all rates to monthly, add 1 to them and divide by (1+inflation)
mortgage_30Y_monthly = pd.merge(mortgage_30Y_monthly, inflation, on = 'Date')
mortgage_5_1_monthly = pd.merge(mortgage_5_1_monthly, inflation, on = 'Date')
tnote_10Y_monthly = pd.merge(tnote_10Y_monthly, inflation, on = 'Date')

CBond_monthly = pd.merge(CBond_monthly, inflation, on = 'Date')
A_monthly = pd.merge(A_monthly, inflation, on = 'Date')
BBB_monthly = pd.merge(BBB_monthly, inflation, on = 'Date')

SP500_ret = pd.merge(SP500_ret, inflation, on = 'Date')
DJI_ret = pd.merge(DJI_ret, inflation, on = 'Date')
nasdaq_ret = pd.merge(nasdaq_ret, inflation, on = 'Date')

mortgage_30Y_monthly['infl_adj_EAR'] = ( ((mortgage_30Y_monthly['EAR']/100)+1)/((mortgage_30Y_monthly['inflation']/100)+1) - 1 )*100
mortgage_5_1_monthly['infl_adj_EAR'] = ( ((mortgage_5_1_monthly['EAR']/100)+1)/((mortgage_5_1_monthly['inflation']/100)+1) - 1 )*100
tnote_10Y_monthly['infl_adj_yield'] = ( ((tnote_10Y_monthly['Value']/100)+1)/((tnote_10Y_monthly['inflation']/100)+1) - 1 )*100

CBond_monthly['infl_adj_yield'] = ( ((CBond_monthly['yield']/100)+1)/((CBond_monthly['inflation']/100)+1) - 1 )*100
A_monthly['infl_adj_yield'] = ( ((A_monthly['yield']/100)+1)/((A_monthly['inflation']/100)+1) - 1 )*100
BBB_monthly['infl_adj_yield'] = ( ((BBB_monthly['yield']/100)+1)/((BBB_monthly['inflation']/100)+1) - 1 )*100

SP500_ret['infl_adj_EAR'] = ( ((SP500_ret['return']/100)+1)/((SP500_ret['inflation']/100)+1) - 1 )*100
DJI_ret['infl_adj_EAR'] = ( ((DJI_ret['return']/100)+1)/((DJI_ret['inflation']/100)+1) - 1 )*100
nasdaq_ret['infl_adj_EAR'] = ( ((nasdaq_ret['return']/100)+1)/((nasdaq_ret['inflation']/100)+1) - 1 )*100

# Visualization
fig1, ax1 = plt.subplots()
fig1.suptitle('US Benchmarks')
ax1.set_xlabel('date')
ax1.set_ylabel('returns (%)')
ax1.plot(inflation['inflation'], label = 'Inflation')
ax1.plot(tnote_10Y['Value'], label = 'T-note 10 year (nominal)')
ax1.legend()

fig2, ax2 = plt.subplots()
fig2.suptitle('US Personal Debt Returns $\it{real}$')
ax2.set_xlabel('date')
ax2.set_ylabel('returns (%)')
ax2.plot(mortgage_30Y_monthly['infl_adj_EAR'], label = 'Fixed mortgage 30 year')
ax2.plot(mortgage_5_1_monthly['infl_adj_EAR'], label = 'Adjustable mortgage 5/1')
ax2.plot(tnote_10Y_monthly['infl_adj_yield'], label = 'T-note 10 year (ref)')
ax2.grid(True)
ax2.legend()

fig3, ax3 = plt.subplots()
fig3.suptitle('US Corporate Debt Returns $\it{real}$')
ax3.set_xlabel('date')
ax3.set_ylabel('returns (%)')
ax3.plot(CBond_monthly['infl_adj_yield'], label = 'US Corporate Bonds')
ax3.plot(A_monthly['infl_adj_yield'], label = 'A Bonds')
ax3.plot(BBB_monthly['infl_adj_yield'], label = 'BBB Bonds')
ax3.plot(tnote_10Y_monthly['infl_adj_yield'], label = 'T-note 10 year (ref)')
ax3.grid(True)
ax3.legend()

fig4, ax4 = plt.subplots()
fig4.suptitle('US Stock Returns $\it{real}$')
ax4.set_xlabel('date')
ax4.set_ylabel('returns (%)')
ax4.plot(SP500_ret['infl_adj_EAR'].rolling(6).mean(), label = 'S&P500 rolling mean')
ax4.plot(DJI_ret['infl_adj_EAR'].rolling(6).mean(), label = 'DJI rolling mean')
ax4.plot(nasdaq_ret['infl_adj_EAR'].rolling(6).mean(), label = 'NASDAQ rolling mean')
ax4.plot(tnote_10Y_monthly['infl_adj_yield'], label = 'T-note 10 year (ref)')
ax4.grid(True)
ax4.legend()

plt.show()
