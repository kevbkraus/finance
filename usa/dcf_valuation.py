# dcf_valuation.py -------------------------------------------------------------------------------
#   Carries out discounted cashflow valuation of a company. The code isn't meant to be a substitute
# for a thorough analysis. It is supposed to help us narrow down, using software, to a small 
# collection of stocks on which we can do a thorough analysis. The user needs to be aware of the 
# following short comings of the code:
#
# 1. It considers all cashflows to be coming from the U.S. and applies a single ERP in the
#    calculations. But in reality, a company's revenue may be coming from many countries and one
#    would have to get a weighted average ERP
# 2. Beta used is USA's. If the revenue of the company is coming from several countries around the
#    globe, then a global beta should actually be used
# 3. Majority, minority cross holdings cannot be discerned by looking at the statements as supplied
#    by AlphaVantage. So they go unnaccounted for
# 4. BV of debt is used while calculating levered beta as well as WACC, whereas we should ideally 
#    use MV of debt
# 5. For WACC, we should use actual debt rating from one of the rating agencies. However, we use
#    prof. Damodaran's synthetic rating method as finding the actual rating is impractical 
# ------------------------------------------------------------------------------------------------

import requests
import json
import numpy as np
import pandas as pd

import os
import sys
import errno
import time
from datetime import datetime
from tqdm import tqdm, trange
import argparse
import quandl

def get_statements(symbol):
    AV_URL = "https://www.alphavantage.co/query"
    AV_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')

    # NOTE: Alpha vantage always seems to give consolidated statements and not standalone. Net income figure seems to be net income attributable -
    # to controlling interest, which is the right thing to do
    subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', symbol, 'income_statement'], capture_output=True)
    subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', symbol, 'cashflow'], capture_output=True)

# Parse command line arguments
msg = "Carries out DCF based valuation of a company"
parser = argparse.ArgumentParser(description=msg)
parser.add_argument('symbol', help="ticker symbol")
parser.add_argument('-i', '--industry', help="Name of the industry according to adamodaran betas.xls")

args = parser.parse_args()

# Get latest information related to risk free rate


# In-code input parameters
rfr = quandl.get('USTREASURY/YIELD').iloc[-1]['10 YR'] # %. Risk free rate for USA. We use the latest 10 year treasury yield.
erp = 4.31 # %. Equity risk premium for USA
tax = 25 # %. Tax rate. One can use effective or marginal. This changes based on state of registration.-
         # But we will use a single figure that stands for all states. 
steady_beta = 1 # no unit. Beta to be used for the steady growth stage 


# Get beta to use from adamodaran's xls
tempdf = pd.read_excel('/home/dinesh/Documents/Valuations/adamodaran/betas.xls', 'Industry Averages', skiprows=9, index_col=0)
unlevered_beta = tempdf.loc['Advertising']['Unlevered beta corrected for cash']

# Get market cap, outstanding shares and stock price
query_params = { "function": 'OVERVIEW', "symbol": symbol, "apikey": AV_KEY}
response = (requests.get(AV_URL, params=query_params)).json()
mv_equity = int(response['MarketCapitalization'])
outstanding_shares = int(response['SharesOutstanding'])
price = float(response['200DayMovingAverage'])


# Get financial statements # TODO: Create TTM and use it instead
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Process balance sheet
filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_quarterly.csv'
try:
    bsheet = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe 

# Process income statements
filename = consolidated_prices_folder + '/income_statements/' + symbol + '_quarterly.csv'
try:
    incstmt = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe 

inc_ttm = incstmt.iloc[0:4].sum() # Sum up all items of latest 4 quarters 
inc_ttm.fiscalDateEnding = incstmt.iloc[0].fiscalDateEnding # Date and currency get added up to nonsensical values in the above operation -
inc_ttm.reportedCurrency = incstmt.iloc[0].reportedCurrency #. So correct them to sensible values

# Process cashflow statement
filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_quarterly.csv'
try:
    cashflowstmt = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe

cashflow_ttm = cashflowstmt.iloc[0:4].sum() # Sum up all items of latest 4 quarters 
cashflow_ttm.fiscalDateEnding = cashflowstmt.iloc[0].fiscalDateEnding # Date and currency get added up to nonsensical values in the above operation -
cashflow_ttm.reportedCurrency = cashflowstmt.iloc[0].reportedCurrency #. So correct them to sensible values

# Create a dataframe of selected financial data
fundamentals = pd.DataFrame(columns=['date', 'cash', 'debt', 'revenue', 'r_and_d', 'opinc', 'intexp', 'netinc', 'netcapex', 'changeinwc'])
fundamentals.loc[0, 'date'] = bsheet.loc[0, 'fiscalDateEnding'] 
fundamentals.loc[0, 'cash'] = bsheet.loc[0, 


fundamentals['date'] = bsheet['fiscalDateEnding']
bsheet[bsheet['fiscalDateEnding'] == fundamentals['date']]
all(bsheet['fiscalDateEnding'] == fundamentals['date'])





