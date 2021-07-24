# get_raw_fundamentals.py -----------------------------------------------------------------------------
#   Imports csv data (originally obtained from Alpha Vantage) from balance sheet, income statement and
# cashflow statement of a given company into dataframes for the user to then play with
# -----------------------------------------------------------------------------------------------------
import requests
import json
import numpy as np
import pandas as pd
import os
import sys
import errno
import time
from datetime import datetime
from datetime import date

def get_raw_fundamentals(symbol):
    consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
    response = dict.fromkeys({'result', 'reason for failure', 'bsttm', 'isttm', 'cfttm', 'bs', 'is', 'cf'}) 
    response['result'] = 'failure' # Init this to failure so that if error occurs during execution, we can simply -
    
    # Process balance sheet
    filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_quarterly.csv'
    try:
        bsheetq = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    response['bsttm'] = bsheetq
    
    # Process income statements
    filename = consolidated_prices_folder + '/income_statements/' + symbol + '_quarterly.csv'
    try:
        incstmtq = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    response['isttm'] = incstmtq
    
    # Process cashflow statement
    filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_quarterly.csv'
    try:
        cashflowstmtq = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe
    response['cfttm'] = cashflowstmtq
    
    
    # Bring in annual statments so we can extract historical data
    filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_annual.csv'
    try:
        bsheet = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    response['bs'] = bsheet
    
    filename = consolidated_prices_folder + '/income_statements/' + symbol + '_annual.csv'
    try:
        incstmt = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    response['is'] = incstmt
    
    filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_annual.csv'
    try:
        cashflow = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe
    response['cf'] = cashflow
    
    response['result'] = 'success' # Init this to failure so that if error occurs during execution, we can simply -
    return(response)  # Return an empty dataframe


