import pandas as pd
import ssl

from edgar_utils import ticker_to_cik, get_financial_item
from adamodaran_utils import extract_industry_tickers

# INPUTS
# I use Prof. Damodaran's indname.xls to find companies that belong to an industry. You must enter industry name(s) -
# exactly the way they are specified in indname.xls, sheet 'US by industry'. You can find the xl sheet here: -
# https://www.stern.nyu.edu/~adamodar/pc/datasets/indname.xls
industries_of_interest = ["Shoe"]   # A list of industries that you are interested in

# You need to specify the financial item you are interested in the way the item is mentioned in EDGAR's database. To -
# familiarlize yourself with EDGAR's terminology, please check out -
# https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json
financial_item_of_interest = "ResearchAndDevelopmentExpense"
print("Code execution begins")
# CODE

# Create a list of CIK values corresponding to the companies we are interested in. 
# Explanation: Prof. Damodaran's indname.xls comtains all the U.S. companies and the industries they belong to. 
# The file contains ticker symbols of companies in <stock exchange name>:<Ticker> format. But EDGAR APIs use 
# 10-digit CIK values for companies. So we use first extract the Ticker symbols of the companies that belong to -
# the industries we are interested in and then use a mapping between Ticker symbols and CIK values from EDGAR 
# website to create a list of CIK values
ticker_list = extract_industry_tickers(industries_of_interest)
ticker_list.sort()  # Sorting it so that we can manually verify if the cik values extracted for tickers are right. -
                    # This just makes debugging easy. It doesn't serve any functional purpose

ticker_list = ['AAPL', 'MSFT','NVDA']
cik_list = ticker_to_cik(ticker_list)
financial_item_of_interest = "AccountsPayableCurrent"
cik_str = cik_list[0]
AccountsPayable_df = get_financial_item(cik_str, financial_item_of_interest)
print("Dummy")