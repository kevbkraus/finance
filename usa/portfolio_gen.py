# portfolio_gen.py -------------------------------------------------------------------------------------
#   Generates portfolios comprising of one stock from each GICS sector in a randomized fasjion using
# the following algorithm
#   1. Shortlist SP500 stocks using a criteria
#   2. Seelect a sector at random
#   3. Find the stock with the best return per risk stock in that sector that hasn't been already chosen
#   4. Select at random one among remaining sectors, find the stock that has the least correlation with
#      already chosen and add to it and create a portfolio
#   5. Continue step 4 until all sectors have been exhausted. Save the portfolio
#   6. Repeat steps 1 to 5 as many times as needed
# ------------------------------------------------------------------------------------------------------

import requests
import json
import math
import numpy as np
import pandas as pd

import os
import sys
import errno
from tqdm import tqdm, trange
import argparse

# Function definitions
# get_bsheet ------------------------------------------------------------------------------------
#   Checks if the file corresponding to the balance sheet in question is present and the numbers
#   are indeed numbers and not strings. If yes, gets the data. If not, downloads the data from the
#   internet
#
# Inputs:
#   ticker: Ticker symbol for the security
#
# Outputs:
#   A pandas dataframe containing balance sheet info
#
# -------------------------------------------------------------------------------------------------
def get_bsheet(security):
    filename = consolidated_prices_folder + '/balance_sheets/' + security + '_annual.csv' # the company is probably a going concern winding up   
    if not os.path.exists(filename):
        subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', security, 'balance_sheet'], capture_output=True)
    try:
        bsheet = pd.read_csv(filename, index_col=0, parse_dates=True)
    except Exception as e:
        print("Unexpected error while trying to open", filename, ". Error: ", e)
        print("Filtering out ", security, " to be on the safer side")
        return(pd.DataFrame())  # Return an empty dataframe 
   
    # This is done because of a flaw in earlier version of download software
    # stored stored 'None' as is and hence even if one 'None' is present in a 
    # column read_csv assumes everything in the column, including numbers are strings
    if (isinstance(bsheet.iloc[0].retainedEarnings, str) or          
        isinstance(bsheet.iloc[0].totalCurrentAssets, str) or      
        isinstance(bsheet.iloc[0].totalCurrentLiabilities,str)) :   
        subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', security, 'balance_sheet'], capture_output=True)
    try:
        bsheet = pd.read_csv(filename, index_col=0, parse_dates=True)
    except Exception as e:
        print("Unexpected error while trying to open", filename, ". Error: ", e)
        print("Filtering out ", security, " to be on the safer side")
        return(pd.DataFrame())  # Return an empty dataframe 

    bsheet.sort_values(by='fiscalDateEnding', axis='index', ascending = False, inplace=True)    # Sort so we can pull the latest data
    return(bsheet)

# Parameters
consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'

# Filter stocks based on a criteria
# Sidestep minefields  
yinfo_filename = consolidated_prices_folder + '/yinfo.csv'
stock_ratios = pd.read_csv(yinfo_filename, index_col=0)
stock_ratios = stock_ratios[stock_ratios['priceToBook'].notna()]    # price to book = NA implies book value 
                                                                    # of equity is negative
stock_ratios = stock_ratios[stock_ratios['trailingEps'] > 0]    # Getting rid of companies losing money

symbols = list(stock_ratios.index)
retained_symbols = list()
for symbol in tqdm(symbols, desc="Checking retained earnings"):              # If retained earnings are continually negative, 
    bsheet = get_bsheet(security=symbol)
    if bsheet.empty:
        continue
    
    if (math.isnan(bsheet.iloc[0].retainedEarnings) or 
        math.isnan(bsheet.iloc[1].retainedEarnings)):
        continue                            # Sometimes, the retainedEarnings is empty. In that case, just skip the symbol
    
    if (bsheet.iloc[0].retainedEarnings < 0 and 
        bsheet.iloc[0].retainedEarnings < bsheet.iloc[1].retainedEarnings):
        continue    # Continuing means filtering out this symbol
    
    retained_symbols.append(symbol)

# Rank resulting symbols based on some criteria
stock_ratios.dropna(axis='columns', how='all', inplace=True)   # Drp empty columns to avoid unnecessary warning prints during next line execution
median_ratios = stock_ratios.median(skipna=True)
ratings_df = pd.Series(index=retained_symbols, name = 'rating')
for symbol in tqdm(ratings_df.index, desc='Rating stocks'): 
    bsheet = get_bsheet(security=symbol)
    if bsheet.empty:
        continue
    
    ratings_df[symbol] = 1  # We start with one star rating    

    if (math.isnan(bsheet.iloc[0].retainedEarnings) or 
        math.isnan(bsheet.iloc[1].retainedEarnings)):
        continue                            # Sometimes, the retainedEarnings is empty. In that case, just skip the symbol

    if (bsheet.iloc[0].totalCurrentAssets - bsheet.iloc[0].totalCurrentLiabilities > 0 and
        (not math.isnan(bsheet.iloc[0].totalCurrentAssets)) and
        (not math.isnan(bsheet.iloc[0].totalCurrentLiabilities))):
        ratings_df[symbol] = ratings_df[symbol]+1 # If working capital is positive give one extra star
   
    if stock_ratios.loc[symbol, 'trailingPE'] < median_ratios.trailingPE:
        ratings_df[symbol] = ratings_df[symbol]+1 # If PE is in the lower half of PEs give one extra star

    if stock_ratios.loc[symbol, 'profitMargins'] > 0:      # During covid times, many companies have performed poorly. Later it is better to 
        ratings_df[symbol] = ratings_df[symbol]+1   # make this a filtering out criteria instead of a rating criteria
        if stock_ratios.loc[symbol, 'profitMargins'] > stock_ratios[stock_ratios['profitMargins']>0].median(skipna=True).profitMargins:   # If the profit margin is larger than 
                                                                                                        # median margins among positive margin companies..            
            ratings_df[symbol] = ratings_df[symbol]+1   

ratings_df.to_csv(consolidated_prices_folder + 'ratings.csv') 
