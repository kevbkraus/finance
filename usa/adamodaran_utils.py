import openpyxl
import sys
import os
import pandas as pd
import requests

def extract_industry_tickers(industry_list):
    local_dir_name = os.path.dirname(__file__)
    indname_file_path = local_dir_name + "\\" + "indname.xls"
    if os.path.exists(indname_file_path):
        industry_df = pd.read_excel(indname_file_path, sheet_name="US by industry")
    else:
        #industry_df = pd.read_excel("https://www.stern.nyu.edu/~adamodar/pc/datasets/indname.xls", sheet_name="US by industry")
        resp = requests.get("https://www.stern.nyu.edu/~adamodar/pc/datasets/indname.xls", verify=False)
        with open(indname_file_path, "wb") as f:  
            f.write(resp.content) 
        industry_df = pd.read_excel(indname_file_path, sheet_name="US by industry")

    valid_industry_values = industry_df["Industry Group"].unique()

    # Sanity check
    if not set(industry_list).issubset(set(valid_industry_values)):
        print("One or more industry values you input is wrong. The following are valid values")
        for indname in valid_industry_values:
            print(indname)
        sys.exit("Input Error")

    exchange_ticker_list = list(industry_df.loc[industry_df["Industry Group"].isin(industry_list), 'Exchange:Ticker'])   # Extract only rows that correspond 
                                                                                                # to the industries we are interested in  
    ticker_list = list(map(lambda s:s.split(":")[1], exchange_ticker_list))
    return(ticker_list)