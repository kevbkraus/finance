import pandas as pd
#import ssl
import openpyxl
import json
#import os

#ssl._create_default_https_context = ssl._create_unverified_context

indname_file_path = "C:/Users/dinesh/OneDrive - Fordham University/Finance/adamodaran/indname.xls"
# Specify the industry group. The following are valid values:

# 
# industry_df = pd.read_excel("https://www.stern.nyu.edu/~adamodar/pc/datasets/indname.xls", sheet_name="US by industry", )
industries = ["Semiconductor", "Semiconductor Equip"]

# Stage 1: Get the CIK values of the companies we are interested in
industry_df = pd.read_excel(indname_file_path, sheet_name="US by industry")
valid_industry_values = industry_df["Industry Group"].unique()
if set(industries).issubset(set(valid_industry_values)):
    sub_industry_df = industry_df[industry_df["Industry Group"] == industries[0]] # TODO: Make this work for the entire list industries
    ticker_list = list(sub_industry_df["Exchange:Ticker"])
    
    tickers_wo_exchange = []
    for ticker in ticker_list:  # TODO: Convert this into a iter or something more efficient
        tickers_wo_exchange.append(ticker.split(":")[1])

    cik_map = pd.read_excel(indname_file_path, sheet_name="CIK map")
    cik_list = []
    for ticker in tickers_wo_exchange:  # Make this more efficient
        try:
            cik_list.append(cik_map[cik_map['Ticker'] == ticker]['CIK'].values[0])
        except:
            continue
else:
    print("One or more industry values you input is wrong. The following are valid values")
    for ind in valid_industry_values:
        print(ind)


# Stage 2: Create a list of filenames from CIK list we created in Stage 1
# Create filenames from the cik_list
fnames = []
filename_seed = "CIK0000000000"
for cik in cik_list:
    cik_str = str(cik)
    filename = filename_seed[:3+10-len(cik_str)]+cik_str+".json"
    fnames.append(filename)

# Stage 3: Pull a financial item of interest from all the companies in the industry in which we are interested.
# This corresponds to the companies whose CIK is in the CIK list we created in Stage 1
item_of_interest_name =  "ResearchAndDevelopmentExpense"
item_type = "flow" # For IS and CFO item, use "flow". For BS item, use ""
if item_type == "flow":
    item_cols = ['company','cik','start','end','val','form']
else:
    item_cols = ['company','cik','end','val','form']
for filename in fnames:
    filepath = "C:/Users/dinesh/Edgar/companyfacts/"+filename
    try:
        raw_json_data = open(filepath)
    except Exception as exc:
        print(exc)
        continue

    company_data = json.load(raw_json_data)
    try:
        item_of_interest = company_data['facts']['us-gaap'][item_of_interest_name]
    except:
        continue

    item_dictionary = dict.fromkeys(item_cols)
    item_df = pd.DataFrame(columns=item_cols)
    for financial in item_of_interest['units']['USD']:
        for dict_col in item_cols:
            if dict_col in ['company','cik']:
                continue
            else:
                item_dictionary[dict_col] = financial[dict_col]

        item_df = item_df.

# returns JSON object as a dictionary
#data = json.load(f)
print("dum")

