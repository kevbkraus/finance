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
from scipy import stats

import os
import sys
import subprocess
import errno
import time
from datetime import datetime
from datetime import date
from tqdm import tqdm, trange
import argparse
import quandl
from openpyxl import load_workbook


# get_statements -----------------------------------------------------------------------------------------------------------------
#   Downloads most updated financial statements from Alpha Vantage
# --------------------------------------------------------------------------------------------------------------------------------
def get_statements(symbol):
    AV_URL = "https://www.alphavantage.co/query"
    AV_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')

    # NOTE: Alpha vantage always seems to give consolidated statements and not standalone. Net income figure seems to be net income attributable -
    # to controlling interest, which is the right thing to do
    statements = ['balance_sheet', 'income_statement', 'cashflow']

    for statement in statements:
        subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', symbol, statement], capture_output=True)
        if 'Note' in str(subp_resp.stdout): # Alpha Vantage limit (5 req per min) reached. download_statements already waits of 60s.- 
                                              # So just try one more time
            print('AV limit reached. Trying one more time')
            subp_resp = subprocess.run(['python3', 'download_statements.py', '-t', symbol, statement], capture_output=True)
        


# get_fundamentals ---------------------------------------------------------------------------------------------------------------
#   Gets financial statements, creates TTM and carries out sanity checks 
# --------------------------------------------------------------------------------------------------------------------------------
def get_fundamentals(symbol):
    consolidated_prices_folder = '/home/dinesh/Documents/security_prices/usa'
    response = dict.fromkeys({'result', 'reason for failure', 'fundamentals'}) 
    response['result'] = 'failure' # Init this to failure so that if error occurs during execution, we can simply -
    
    # Process balance sheet
    filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_quarterly.csv'
    try:
        bsheetq = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    
    # Process income statements
    filename = consolidated_prices_folder + '/income_statements/' + symbol + '_quarterly.csv'
    try:
        incstmtq = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    
    inc_ttm = incstmtq.iloc[0:4].sum() # Sum up all items of latest 4 quarters 
    inc_ttm['fiscalDateEnding'] = incstmtq.loc[0, 'fiscalDateEnding'] # Date and currency get added up to nonsensical values in the above operation -
    inc_ttm['reportedCurrency'] = incstmtq.loc[0, 'reportedCurrency'] #. So correct them to sensible values
    
    # Process cashflow statement
    filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_quarterly.csv'
    try:
        cashflowstmtq = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe
    
    cashflow_ttm = cashflowstmtq.iloc[0:4].sum() # Sum up all items of latest 4 quarters 
    cashflow_ttm['fiscalDateEnding'] = cashflowstmtq.loc[0, 'fiscalDateEnding'] # Date and currency get added up to nonsensical values in the above operation -
    cashflow_ttm['reportedCurrency'] = cashflowstmtq.loc[0, 'reportedCurrency'] #. So correct them to sensible values
    
    # Bring in annual statments so we can extract historical data
    filename = consolidated_prices_folder + '/balance_sheets/' + symbol + '_annual.csv'
    try:
        bsheet = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    
    filename = consolidated_prices_folder + '/income_statements/' + symbol + '_annual.csv'
    try:
        incstmt = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe 
    
    filename = consolidated_prices_folder + '/cashflow_statements/' + symbol + '_annual.csv'
    try:
        cashflow = pd.read_csv(filename, parse_dates=['fiscalDateEnding']).fillna(0)
    except Exception as e:
        response['reason for failure'] = "Unexpected error while trying to open" + filename 
        return(response)  # Return an empty dataframe
    
    # Do sanity check
    if not (inc_ttm.fiscalDateEnding == bsheetq.iloc[0].fiscalDateEnding == cashflow_ttm.fiscalDateEnding):
        response['reason for failure'] = "Dates on TTM statements aren't matching"
        return(response)
  
    statement_years = min(bsheet.shape[0], incstmt.shape[0], cashflow.shape[0]) # Sometimes one statment has more historical data than others  
    if not (all(bsheet.loc[0:statement_years-1, 'fiscalDateEnding'] == incstmt.loc[0:statement_years-1, 'fiscalDateEnding']) and  # NOTE: loc and iloc work differently while fetching
            all(incstmt.loc[0:statement_years-1, 'fiscalDateEnding'] == cashflow.loc[0:statement_years-1, 'fiscalDateEnding'])): # rows. loc[0:3 returns 4 rows, iloc[0:3 returns 3
        response['reason for failure'] = "Dates on yearly statements aren't matching"
        return(response)
        
    # ---------------------------------- Create a dataframe of selected financial data -----------------------------------------------
    # This is the starting point of actually valuing the company
    # NOTE: From this point on, we deal with Millions of $ 
    # --------------------------------------------------------------------------------------------------------------------------------
    fundamentals = pd.DataFrame(columns=['date', 'cash', 'equity', 'debt', 'revenue', 'RnD', 'opinc', 'intexp', 'netinc', 'netcapex', 'changeinwc'])
    
    fundamentals.loc[0, 'date'] = bsheetq.loc[0, 'fiscalDateEnding'].date() 
    fundamentals.loc[0, 'cash'] = bsheetq.loc[0, 'cashAndShortTermInvestments']/1E6 + bsheetq.loc[0, 'longTermInvestments']/1E6
    fundamentals.loc[0, 'equity'] = bsheetq.loc[0, 'totalShareholderEquity']/1E6
    fundamentals.loc[0, 'debt'] = bsheetq.loc[0, 'currentDebt']/1E6 + bsheetq.loc[0, 'longTermDebtNoncurrent']/1E6
    if pd.isna(inc_ttm['nonInterestIncome']) or inc_ttm['nonInterestIncome'] < 0:
        fundamentals.loc[0, 'revenue'] = inc_ttm['totalRevenue']/1E6    # For whatever reason, Alpha Vantage seems to have changed the definition of - 
    else:                                                               # some revenue related terms post 2017
        fundamentals.loc[0, 'revenue'] = inc_ttm['nonInterestIncome']/1E6
    
    fundamentals.loc[0, 'RnD'] = inc_ttm['researchAndDevelopment']/1E6
    fundamentals.loc[0, 'opinc'] = inc_ttm['operatingIncome']/1E6
    fundamentals.loc[0, 'intexp'] = inc_ttm['interestExpense']/1E6
    fundamentals.loc[0, 'netinc'] = inc_ttm['netIncome']/1E6
    
    fundamentals.loc[0, 'netcapex'] = cashflow_ttm['capitalExpenditures']/1E6 - cashflow_ttm['depreciationDepletionAndAmortization']/1E6
    fundamentals.loc[0, 'changeinwc'] = cashflow_ttm['changeInInventory']/1E6 + cashflow_ttm['changeInReceivables']/1E6 \
                                        - (bsheetq.loc[0, 'currentAccountsPayable']/1E6 - bsheet.loc[0, 'currentAccountsPayable']/1E6)
    
    for i in range(0,statement_years): 
        fundamentals.loc[i+1, 'date'] = bsheet.loc[i, 'fiscalDateEnding'].date() 
        fundamentals.loc[i+1, 'cash'] = bsheet.loc[i, 'cashAndShortTermInvestments']/1E6 + bsheet.loc[i, 'longTermInvestments']/1E6
        fundamentals.loc[i+1, 'equity'] = bsheet.loc[i, 'totalShareholderEquity']/1E6
        fundamentals.loc[i+1, 'debt'] = bsheet.loc[i, 'currentDebt']/1E6 + bsheet.loc[i, 'longTermDebtNoncurrent']/1E6
        if pd.isna(incstmt.loc[i, 'nonInterestIncome']) or incstmt.loc[i, 'nonInterestIncome'] < 0:
            fundamentals.loc[i+1, 'revenue'] = incstmt.loc[i, 'totalRevenue']/1E6
        else:    
            fundamentals.loc[i+1, 'revenue'] = incstmt.loc[i, 'nonInterestIncome']/1E6
        fundamentals.loc[i+1, 'RnD'] = incstmt.loc[i, 'researchAndDevelopment']/1E6
        fundamentals.loc[i+1, 'opinc'] = incstmt.loc[i, 'operatingIncome']/1E6
        fundamentals.loc[i+1, 'intexp'] = incstmt.loc[i, 'interestExpense']/1E6
        fundamentals.loc[i+1, 'netinc'] = incstmt.loc[i, 'netIncome']/1E6
        
        if i != statement_years-1: # For the last year there is no point in calculating the following
            fundamentals.loc[i+1, 'netcapex'] = cashflow.loc[i, 'capitalExpenditures']/1E6 - cashflow.loc[i, 'depreciationDepletionAndAmortization']/1E6
            fundamentals.loc[i+1, 'changeinwc'] = cashflow.loc[i, 'changeInInventory']/1E6 + cashflow.loc[i, 'changeInReceivables']/1E6 \
                                                - (bsheet.loc[i, 'currentAccountsPayable']/1E6 - bsheet.loc[i+1, 'currentAccountsPayable']/1E6)
    
    response['result'] = 'success'
    response['fundamentals'] = fundamentals
    return(response)        

def value_company(symbol, industry, fundamentals):
    super_response = dict.fromkeys({'result', 'reason for failure', 'Company name', 'Share price', 'Analyst target', 'PE', 'Debt rating', 'fundamentals', 'value_df'}) 
    super_response['result'] = 'failure' # Init this to failure so that if error occurs during execution, we can simply -
                                         # return super_response     
        
    # Parameters
    AV_URL = "https://www.alphavantage.co/query"
    AV_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')
    
    # Get latest information related to risk free rate
    rfr = 1.42 # NOTE: Temp measure. Should put back to quandl.get('USTREASURY/YIELD').iloc[-1]['10 YR'] # %. Risk free rate for USA. We use the latest 10 year treasury yield.
    
    # In-code input parameters
    erp = 4.31 # %. Equity risk premium for USA
    tax = 25 # %. Tax rate. One can use effective or marginal. This changes based on state of registration.-
             # But we will use a single figure that stands for all states. 
    
    # Get beta to use from adamodaran's xls
    tempdf = pd.read_excel('/home/dinesh/Documents/Valuations/adamodaran/betas.xls', 'Industry Averages', skiprows=9, index_col=0)
    unlevered_beta = tempdf.loc[industry]['Unlevered beta corrected for cash']
    
    # Get market cap, outstanding shares and stock price
    query_params = { "function": 'OVERVIEW', "symbol": symbol, "apikey": AV_KEY}
    response = pd.Series((requests.get(AV_URL, params=query_params)).json())

    if response.empty: 
        super_response['reason for failure'] = 'Empty response while trying to get overview of the stock'
        return(super_response)
    
    if 'Note' in response or 'Alpha Vantage' in str(response):
        super_response['reason for failure'] = 'Alpha Vantage limit reached. Abandoning this company'
        return(super_response)
    
    response.replace('None',np.nan,inplace=True) # Otherwise trying to convert 'None' string to int or float (below) will throw an error
    company_name = response['Name']
    mv_equity = int(response['MarketCapitalization'])
    outstanding_shares = int(response['SharesOutstanding'])
    price = float(response['50DayMovingAverage'])
    analyst_target_price = float(response['AnalystTargetPrice'])
    pe_ratio = float(response['PERatio'])
    
    super_response['Company name'] = company_name
    super_response['Share price'] = price
    super_response['Analyst target'] = analyst_target_price
    super_response['PE'] = pe_ratio
    
    if fundamentals.shape[0] < 5: # At a min, we are expecting 4 historical years, plus the latest year/TTM
        super_response['reason for failure'] = 'We do not have enough historic data to go about'
        return(super_response)
    
    # Capitalize R&D (with 5 year straight line depreciation)
    # We find the average R&D expense and depreciate them as operating expense. The reason we do this is that we are going to find 
    # ROIC and reinvestment rates for DCF valuation by averaging figures over several years in the past. But, we won't be able to 
    # find out the depreciation values of one or more past R&D expenses for the majority of historic data. For example, if we use
    # 5 year historic data, and use 5 year straight line depreciation, no historic data can be used for fiding ROIC, reinvestment
    # rate, because for oldest 4 years, we cannot get accurate depreciated R&D values simply because we don't have R&D data from 
    # the past before the 5-years data we have
    if any(fundamentals['RnD'] < 0): # Sanity check
        super_response['reason for failure'] = 'R&D expense cannot be negative'
        return(super_response)
    
    average_RnD = fundamentals['RnD'].mean()
    RnD_asset = 3*average_RnD # 1+0.8+0.6+0.4+0.2 = 3
    RnD_depreciation = 0.8*average_RnD # R&D expense made one year is depreciated 20% for every year after that. 4*0.2 = 0.8
    
    fundamentals['equity'] = fundamentals['equity'] + RnD_asset
    fundamentals['opinc'] = fundamentals['opinc'] + fundamentals['RnD'] - RnD_depreciation
    fundamentals['netcapex'] = fundamentals['netcapex'] + fundamentals['RnD'] - RnD_depreciation 
    super_response['fundamentals'] = fundamentals
    
    # Calculate ROIC
    invested_capitals = fundamentals['equity']+fundamentals['debt']-fundamentals['cash']
    roics = pd.Series(dtype=float)
    roics.loc[0] = fundamentals.loc[0,'opinc']*(1-tax/100)*2/(invested_capitals[1]+invested_capitals[2]) # For calculating ROIC of TTM, we are taking a shortcut: We -
                                                                                                         # are using the average invested capital of the previous -
                                                                                                         # financial year and the current - instead of finding the 
                                                                                                         # BVs of equity, debt, cash of the correct quarter 12 months
                                                                                                         # ago, adjusting for R&D etc.
    
    iter_len = 5 if len(fundamentals) > 6 else len(fundamentals)-1 # We don't want to consider anything older than 5 years
    for i in range(1,iter_len): # We skip the last one as we don't have information about invested capital before the oldest year
        roics.loc[i] =  fundamentals.loc[i,'opinc']*(1-tax/100)/invested_capitals.loc[i+1]
    
    roics_pos = pd.Series([x for x in roics if x>0]) # Extract only positive ROIC values
    if len(roics_pos) < 3: # We are overall examining 5 historic years and one ttm
        super_response['reason for failure'] = 'This company has too many loss years'
        return(super_response)
    
    roic = stats.gmean(roics_pos.values)    # Geometric mean of positive ROIC values
    
    # Calculate reinvestment rate (rir)
    reinvestments = fundamentals['netcapex'] + fundamentals['changeinwc']
    rirs = pd.Series(dtype=float)
    free_index = 0
    for i in range(0, iter_len):
        if reinvestments[i] < 0: # We don't want to consider negative reinvestments as it will make calculating average rir difficult
            continue 
        if fundamentals.loc[i,'opinc'] < 0: # We don't want to consider years where they incurred a loss
            continue
        rirs.loc[free_index] = reinvestments[i]/(fundamentals.loc[i,'opinc']*(1-tax/100))
        free_index = free_index+1
    
    if len(rirs) < 3: # We are overall examining 5 historic years and one ttm
        rir = 0
    else:
        rir = rirs.mean()
    
    
    # -------------------------------------------- Calculate Weighted Average Cost of Capital ---------------------------------------
    # We use synthetic bond rating (based on interest coverage ratio) to find cost of debt, and use BV of debt in place of MV of debt
    # -------------------------------------------------------------------------------------------------------------------------------
    ## Find cost of debt
    synthetic_rating = pd.DataFrame({'int_cov_ratio': pd.Series([], dtype=float), 
                                     'rating': pd.Series([], dtype=str), 
                                     'spread': pd.Series([], dtype=float)})
    t_int_cov_ratio = [-np.inf, 0.2, 0.65, 0.8, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 3, 4.25, 5.5, 6.5, 8.5] # 't' prefix for 'table'
    t_rating = ['D2/D', 'C2/C', 'Ca2/CC', 'Caa/CCC', 'B3/B-', 'B2/B', 'B1/B+', 'Ba2/BB', 'Ba1/BB+', 'Baa2/BBB', 'A3/A-', 'A2/A', 'A1/A+', 'Aa2/AA', 'Aaa/AAA']
    t_spread = [17.44, 13.09, 9.97, 9.46, 5.94, 4.86, 4.05, 2.77, 2.31, 1.71, 1.33, 1.18, 1.07, 0.85, 0.69] # percentage
    synthetic_rating = pd.DataFrame({'int_cov_ratio':t_int_cov_ratio, 'rating':t_rating, 'spread':t_spread})
    
    int_cov_ratios = pd.Series(dtype=float)
    free_index = 0
    for i in range(0, iter_len):
        if fundamentals.loc[i,'opinc'] < 0: # We don't want to consider years where they incurred a loss
            continue
        int_cov_ratios.loc[free_index] = fundamentals.loc[i, 'opinc']/fundamentals.loc[i, 'intexp']
        free_index = free_index+1
    
    if len(int_cov_ratios) < 4:
        super_response['reason for failure'] = 'This company has too many loss years'
        return(super_response)
    
    int_cov_ratio = int_cov_ratios.mean()
    temp = synthetic_rating['int_cov_ratio'] < int_cov_ratio # Results in a logical series
    rating_index = len(temp[temp])-1
    spread = synthetic_rating.loc[rating_index, 'spread']
    cost_of_debt = rfr + spread # percentage
    debt_rating = synthetic_rating.loc[rating_index, 'rating']
 
    super_response['Debt rating'] = debt_rating 
    
    ## Find cost of equity
    bv_debt = fundamentals.loc[0, 'debt']
    levered_beta = unlevered_beta*(1 + (1-tax/100)*bv_debt/mv_equity)
    cost_of_equity = rfr + levered_beta*erp # percentage
    
    ## Find WACC
    wacc = (mv_equity/(mv_equity + bv_debt))*cost_of_equity + (bv_debt/(mv_equity + bv_debt))*(1-tax/100)*cost_of_debt
    
    
    # -------------------------------------------- DCF calculation -------------------------------------------------------------------
    # We use a growth ramp down model where we get from current growth to growth rate of economy (as decided by risk free rate, and 
    # then settle for growth at the rate of risk free rate
    # --------------------------------------------------------------------------------------------------------------------------------
    output_filename = '/home/dinesh/Documents/Valuations/usa/' + symbol + '.xlsx'
    writer = pd.ExcelWriter(output_filename, engine = 'openpyxl')
    
    steady_state_roic = 0.1 # NOTE: This is an assumption that may need to change from time to time. So keep reevaluating 
    
    value_df = pd.DataFrame(columns=['gslope=3', 'gslope=5', 'gslope=7'], index=['ssBeta=0.8','ssBeta=1', 'ssBeta=1.2'])
    
    sheetmaxrow = 1
    index_num = 0
    for ssbeta in [0.8, 1, 1.2]:
        col_num = 0
        for gslope in [3, 5, 7]:
            pv_df = pd.DataFrame({  'year': pd.Series([], dtype=int),
                                    'post_tax_opinc': pd.Series([], dtype=float), 
                                    'roic': pd.Series([], dtype=float), 
                                    'rir': pd.Series([], dtype=float), 
                                    'growth': pd.Series([], dtype=float), 
                                    'fcff': pd.Series([], dtype=float), 
                                    'pv': pd.Series([], dtype=float) })
            
            fyear = fundamentals.loc[0,'date'].year
            post_tax_opinc = fundamentals.loc[0, 'opinc']*(1-tax/100)
            fcff = post_tax_opinc - reinvestments[0]
            pv = np.nan
            iroic = roic
            irir = rir
            steady_state_rir = (rfr/100)/steady_state_roic
                
            pv_df.loc[0, 'year'] = fyear
            pv_df.loc[0, 'post_tax_opinc'] = post_tax_opinc
            pv_df.loc[0, 'roic'] = iroic*100
            pv_df.loc[0, 'rir'] = irir*100
            pv_df.loc[0, 'growth'] = iroic*irir*100
            pv_df.loc[0, 'fcff'] = fcff
            pv_df.loc[0, 'pv'] = pv
            if roic*rir < rfr/100: # If growth is already slower than risk free rate. Then treat this as a going concern
                if fcff < 0: # If free cash flow for current year is negative and growth is below rfr, quit automatic valuation and settle for manual valuation
                    super_response['reason for failure'] = 'Negative FCFF for base year'
                    return(super_response)
                op_asset_value = fcff*(1+roic*rir)/(wacc/100 - roic*rir)
            else: 
                num_extord_years = int((roic*rir*100-rfr)/gslope)+3 # NOTE: The y-intercept value of 3 is chosen arbitrarily for now. One should 
                                                                    # however look at hisotric figures what should be the y-intercept
                for i in range(1, num_extord_years+2):
                    fyear = fyear+1
                    post_tax_opinc = post_tax_opinc*(1+iroic*irir)
                    iroic = (steady_state_roic - iroic)/(num_extord_years+1 - (i-1)) + iroic # (y2-y1)/(x2-x1)  * (x-x1) + y1, except, x-x1 is always 1 (year)    
                    irir = (steady_state_rir - irir)/(num_extord_years+1 - (i-1)) + irir # (y2-y1)/(x2-x1)  * (x-x1) + y1, except, x-x1 is always 1 (year)    
                    fcff = post_tax_opinc*(1-irir)
                    if i != num_extord_years+1:
                        pv = fcff/(1+wacc/100)**i
                    else:
                        pv = (fcff/(ssbeta*erp/100))/(1+wacc/100)**(i-1)
                
                    pv_df.loc[i, 'year'] = fyear
                    pv_df.loc[i, 'post_tax_opinc'] = post_tax_opinc
                    pv_df.loc[i, 'roic'] = iroic*100
                    pv_df.loc[i, 'rir'] = irir*100
                    pv_df.loc[i, 'growth'] = iroic*irir*100
                    pv_df.loc[i, 'fcff'] = fcff
                    pv_df.loc[i, 'pv'] = pv
                 
                op_asset_value = pv_df.pv.sum()
            
            firm_value = op_asset_value + fundamentals.loc[0, 'cash']
            equity_value = firm_value - fundamentals.loc[0, 'debt']
            vps = (equity_value*1E6)/outstanding_shares   
            
            value_df.iloc[[index_num],[col_num]] = vps
            col_num = col_num+1
            
            dummy_df = pd.DataFrame([],columns=['ssBeta = ' + str(ssbeta) + ', gslope = ' + str(gslope)]) # Just to write a heading text to the excel sheet
            dummy_df.to_excel(writer, 'Details', index=False, startrow = sheetmaxrow)
            pv_df.to_excel(writer, 'Details', index=False, startrow = writer.book['Details'].max_row)
            sheetmaxrow = writer.book['Details'].max_row+2
    
        index_num = index_num+1
    
    writer.save()
    writer.close()
    super_response['value_df'] = value_df
    
    
    # ------------------------------------------------- Write data to a spreadsheet ---------------------------------------------------------------
    output_filename = '/home/dinesh/Documents/Valuations/usa/' + symbol + '.xlsx'
    book = load_workbook(output_filename)
    writer = pd.ExcelWriter(output_filename, engine = 'openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    
    top_df = pd.DataFrame([[company_name], [symbol], [date.today()], ['USD'], [industry]],
                          index = ['Company name', 'Symbol', 'Date', 'Currency', 'Industry'])  
    
    top_df.to_excel(writer,'Summary', header=False)
    
    rates_df = pd.DataFrame([['risk-free rate',rfr], ['equity risk premium',erp], ['tax',tax]], columns=['RATES','percentage'])
    rates_df.to_excel(writer, 'Summary', index=False, startrow = writer.book['Summary'].max_row+2)
    
    market_df = pd.DataFrame([['market cap',mv_equity], ['stock price',price], ['outstanding shares',outstanding_shares], 
                              ['unlevered beta', unlevered_beta], ['debt rating', synthetic_rating.loc[rating_index,'rating']]], columns=['MARKET FIGURES',''])
    market_df.to_excel(writer, 'Summary', index=False, startrow = writer.book['Summary'].max_row+2)
    
    dummy_df = pd.DataFrame([],columns=['FUNDAMENTALS']) # Just to write a heading text to the excel sheet
    dummy_df.to_excel(writer, 'Summary', index=False, startrow = writer.book['Summary'].max_row+2)
    fundamentals.to_excel(writer, 'Summary', index=False, startrow = writer.book['Summary'].max_row)
    
    derived_df = pd.DataFrame([ ['levered beta', levered_beta], ['cost of equity',cost_of_equity], ['cost of debt', cost_of_debt], ['wacc',wacc],
                                ['return on capital',pv_df.loc[0, 'roic']], ['reinv rate',pv_df.loc[0,'rir']], ['growth rate',pv_df.loc[0,'growth']] ],
                                columns=['DERIVED FIGURES','percentage']) 
    derived_df.to_excel(writer, 'Summary', index=False, startrow = writer.book['Summary'].max_row+2)
    
    dummy_df = pd.DataFrame([],columns=['VPS MATRIX']) # Just to write a heading text to the excel sheet
    dummy_df.to_excel(writer, 'Summary', index=False, startrow = writer.book['Summary'].max_row+2)
    value_df.to_excel(writer, 'Summary', startrow = writer.book['Summary'].max_row)
    
    writer.save()
    writer.close()


    # ---------------------------------------------------- Print out a summary ---------------------------------------------------------------------
    print('\n')
    print('------------------ VALUATION SUMMARY ----------------------')
    print('\n')
    print(company_name, '\n')
    print('Industry: ', industry)
    print('Share price: ', price, '\n')
    print('Analyst target: ',analyst_target_price, '\n')
    print('PE: ', pe_ratio, '\n')
    print('Debt rating: ', debt_rating, '\n')
    print('VPS Matrix')
    print(value_df.to_markdown())
    print('\n Derived Figures')
    print(derived_df.to_markdown())
    print('-----------------------------------------------------------')

    super_response['result'] = 'success'
    return(super_response)
    
