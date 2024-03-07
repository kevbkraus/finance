import requests
import json
import pandas as pd

# ticker_to_cik
# Inputs
#   ticker_list: A list of stock tickers of companies interested in. Ex: ['AAPL', 'MSFT','NVDA']
# Output
#   cik_list: A list of corresponding CIK values (as a 10 digit string)

def ticker_to_cik(ticker_list):
    headers = {'User-Agent': 'Fordham University sthoguluachandraseka@fordham.edu', 'Accept-Encoding': 'gzip,deflate', 'Host':'www.sec.gov'}
    resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
    try:
        map_dict = json.loads(resp.text)   
    except:
        return []   # Return an empty list in case of an error
    
    map_df = pd.DataFrame.from_dict(map_dict, orient="index")
    map_df.sort_values(by='ticker', inplace=True)
    cik_list = list(map_df.loc[map_df['ticker'].isin(ticker_list),'cik_str'])
    cik_seed = "0000000000"
    cik_str_list = []
    for cik in cik_list:
        cik_str = str(cik)
        cik_str_10digit = cik_seed[:10-len(cik_str)]+cik_str
        cik_str_list.append(cik_str_10digit)
    return cik_str_list

# get_financial_item
# Inputs
#   cik_str: 10-digit CIK of the company as a string. Example: 0000320193 (for AAPL). Tip: To find the CIK of a company,
#       go to https://www.sec.gov/edgar/searchedgar/companysearch, and type in the company name (ex. "Apple") and wait
#       for the drop down suggestions show "Apple Inc. (AAPL)". The CIK no. is displayed next to the suggestion. If you 
#       want to copy+paste the CIK, just click on the suggestion, it will take you to the Apple company page in 
#       EDGAR that has all its financial reports and stuff. At the top, expand "Company information" and find the CIK
#       there
#   financial_item_of_interest: IS/BS/CFS item in standard EDGAR terminology. Example: "AccountsPayableCurrent"
#       Tip: To find out the EDGAR standard terms go to https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json . -
#       You will see the latest financial data of Apple. You can scan through it to identify the EDGAR standard term for 
#       whatever financial item you are looking for
# Output
#   data_df: A data frame that contains quarterly, annual values of the financial_item_of_interest for several years

def get_financial_item(cik_str, financial_item_of_interest):
    headers = {'User-Agent': 'Fordham University sthoguluachandraseka@fordham.edu', 'Accept-Encoding': 'gzip,deflate', 'Host':'data.sec.gov'}
    URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK"+cik_str+"/us-gaap/"+ financial_item_of_interest+".json"
    resp = requests.get(URL, headers=headers)
    try:
        data_dict = json.loads(resp.text)   
    except:
        return []   # Return an empty list in case of an error
    
    data_df = pd.DataFrame.from_dict(data_dict['units']['USD'])
    return(data_df)
