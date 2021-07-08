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
#
# WARNING: Some explicit assumptions have been made about AlphaVantage data such as:
# 1. The data fields are uniform across stocks. This is known to be not true! So for some stocks
#    an error will be thrown while accessing some items
# 2. It is assumed that, in all statements, the most recent data appears at the top, followed, 
#    by older data sequentially. TODO: Add a sanity check for this and get rid of this assumption
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
    subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', symbol, 'balance_sheet'], capture_output=True)
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


# --------------------------- Get financial statements, create TTM and carry out sanity checks -----------------------------------
# NOTE: This is a mundane process. One can skip to the next section which gets to the actual valuation part (look for dotted line)
# --------------------------------------------------------------------------------------------------------------------------------
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Process balance sheet
filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_quarterly.csv'
try:
    bsheetq = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe 

# Process income statements
filename = consolidated_prices_folder + '/income_statements/' + symbol + '_quarterly.csv'
try:
    incstmtq = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe 

inc_ttm = incstmtq.iloc[0:4].sum() # Sum up all items of latest 4 quarters 
inc_ttm['fiscalDateEnding'] = incstmtq.loc[0, 'fiscalDateEnding'] # Date and currency get added up to nonsensical values in the above operation -
inc_ttm['reportedCurrency'] = incstmtq.loc[0, 'reportedCurrency'] #. So correct them to sensible values

# Process cashflow statement
filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_quarterly.csv'
try:
    cashflowstmtq = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe

cashflow_ttm = cashflowstmtq.iloc[0:4].sum() # Sum up all items of latest 4 quarters 
cashflow_ttm['fiscalDateEnding'] = cashflowstmtq.loc[0, 'fiscalDateEnding'] # Date and currency get added up to nonsensical values in the above operation -
cashflow_ttm['reportedCurrency'] = cashflowstmtq.loc[0, 'reportedCurrency'] #. So correct them to sensible values

# Bring in annual statments so we can extract historical data
filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_annual.csv'
try:
    bsheet = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe 

filename = consolidated_prices_folder + '/income_statements/' + symbol + '_annual.csv'
try:
    incstmt = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe 

filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_annual.csv'
try:
    cashflow = pd.read_csv(filename, parse_dates=['fiscalDateEnding'])
except Exception as e:
    print("Unexpected error while trying to open", filename, ". Error: ", e)
    sys.exit()  # Return an empty dataframe

# Do sanity check
if not (inc_ttm.fiscalDateEnding == bsheetq.iloc[1].fiscalDateEnding == cashflow_ttm.fiscalDateEnding):
    print("Error: Dates on TTM statements aren't matching")
    sys.exit()

if not (all(bsheet['fiscalDateEnding'] == incstmt['fiscalDateEnding']) and all(incstmt['fiscalDateEnding'] == cashflow['fiscalDateEnding'])):
    print("Error: Dates on yearly statements aren't matching")
    sys.exit()
    
# ---------------------------------- Create a dataframe of selected financial data -----------------------------------------------
# This is the starting point of actually valuing the company
# NOTE: From this point on, we deal with Millions of $ 
# --------------------------------------------------------------------------------------------------------------------------------
fundamentals = pd.DataFrame(columns=['date', 'cash', 'equity', 'debt', 'revenue', 'r_and_d', 'opinc', 'intexp', 'netinc', 'netcapex', 'changeinwc'])

fundamentals.loc[0, 'date'] = bsheetq.loc[0, 'fiscalDateEnding'] 
fundamentals.loc[0, 'cash'] = bsheetq.loc[0, 'cashAndShortTermInvestments']/1E6 + bsheetq.loc[0, 'longTermInvestments']/1E6
fundamentals.loc[0, 'equity'] = bsheetq.loc[0, 'totalShareholderEquity']/1E6
fundamentals.loc[0, 'debt'] = bsheetq.loc[0, 'currentDebt']/1E6 + bsheetq.loc[0, 'longTermDebtNoncurrent']/1E6
if pd.isna(inc_ttm.['nonInterestIncome']) or inc_ttm['nonInterestIncome'] < 0:
    fundamentals.loc[0, 'revenue'] = inc_ttm['totalRevenue']/1E6    # For whatever reason, Alpha Vantage seems to have changed the definition of - 
else:                                                               # some revenue related terms post 2017
    fundamentals.loc[0, 'revenue'] = inc_ttm['nonInterestIncome']/1E6

fundamentals.loc[0, 'r_and_d'] = inc_ttm['researchAndDevelopment']/1E6
fundamentals.loc[0, 'opinc'] = inc_ttm['operatingIncome']/1E6
fundamentals.loc[0, 'intexp'] = inc_ttm['interestExpense']/1E6
fundamentals.loc[0, 'netinc'] = inc_ttm['netIncome']/1E6

fundamentals.loc[0, 'netcapex'] = cashflow_ttm['capitalExpenditures']/1E6 - cashflow_ttm['depreciationDepletionAndAmortization']/1E6
fundamentals.loc[0, 'changeinwc'] = cashflow_ttm['changeInInventory']/1E6 + cashflow_ttm['changeInReceivables']/1E6 \
                                    - (bsheetq.loc[0, 'currentAccountsPayable']/1E6 - bsheet.loc[0, 'currentAccountsPayable']/1E6)

for i in range(0,len(bsheet.index)): 
    fundamentals.loc[i+1, 'date'] = bsheet.loc[i, 'fiscalDateEnding'] 
    fundamentals.loc[i+1, 'cash'] = bsheet.loc[i, 'cashAndShortTermInvestments']/1E6 + bsheet.loc[i, 'longTermInvestments']/1E6
    fundamentals.loc[i+1, 'equity'] = bsheet.loc[i, 'totalShareholderEquity']/1E6
    fundamentals.loc[i+1, 'debt'] = bsheet.loc[i, 'currentDebt']/1E6 + bsheet.loc[i, 'longTermDebtNoncurrent']/1E6
    if pd.isna(incstmt.loc[i, 'nonInterestIncome']) or incstmt.loc[i, 'nonInterestIncome'] < 0:
        fundamentals.loc[i+1, 'revenue'] = incstmt.loc[i, 'totalRevenue']/1E6
    else:    
        fundamentals.loc[i+1, 'revenue'] = incstmt.loc[i, 'nonInterestIncome']/1E6
    fundamentals.loc[i+1, 'r_and_d'] = incstmt.loc[i, 'researchAndDevelopment']/1E6
    fundamentals.loc[i+1, 'opinc'] = incstmt.loc[i, 'operatingIncome']/1E6
    fundamentals.loc[i+1, 'intexp'] = incstmt.loc[i, 'interestExpense']/1E6
    fundamentals.loc[i+1, 'netinc'] = incstmt.loc[i, 'netIncome']/1E6
    
    if i != len(bsheet.index)-1: # For the last year there is no point in calculating the following
        fundamentals.loc[i+1, 'netcapex'] = cashflow.loc[i, 'capitalExpenditures']/1E6 - cashflow.loc[i, 'depreciationDepletionAndAmortization']/1E6
        fundamentals.loc[i+1, 'changeinwc'] = cashflow.loc[i, 'changeInInventory']/1E6 + cashflow.loc[i, 'changeInReceivables']/1E6 \
                                            - (bsheet.loc[i, 'currentAccountsPayable']/1E6 - bsheet.loc[i+1, 'currentAccountsPayable']/1E6)







