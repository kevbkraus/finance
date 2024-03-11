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
# Description
#   Gets the values of a financial item for a company across time
# Inputs
#   cik_str: 10-digit CIK of the company as a string. Example: "0000320193" (for AAPL). Tip: To find the CIK of a company,
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


# get_companywide_concepts(cik_str_list, concepts_of_interest)
# Gets the values of a financial item for several companies (annual, not quarterly) across time
# Inputs
#   cik_str_list: A list of 10-digit CIK of companies as strings. Example: ["0000320193", "0001045810"] 
#       Tip: See the description of get_financial_item to figure out how to find the CIK value of a company 
#   concepts_of_interest: A list of IS/BS/CFS items in standard EDGAR terminology. 
#       Example: ["AccountsPayableCurrent", "ResearchAndDevelopmentExpense"]
#       Tip:  See the description of get_financial_item to figure out how to find standard term for a financial 
#       item of interest
# Output
#   all_companies_dict = A dictionary that has a dataframe for each company with company CIK as the key. The dataframe 
#   for each company has three columns: concept, end and val, 
#   several years of data. 
def get_companywide_concepts(cik_str_list, concepts_of_interest):
    all_companies_dict = dict.fromkeys(cik_str_list, None)
    for company in all_companies_dict:
        headers = {'User-Agent': 'Fordham University sthoguluachandraseka@fordham.edu', 'Accept-Encoding': 'gzip,deflate', 'Host':'data.sec.gov'}
        URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK"+company+".json"
        resp = requests.get(URL, headers=headers)
        try:
            data_dict = json.loads(resp.text)   
        except:
            print("Error while attempting to get info about "+company)
            continue

        concept_dict = dict.fromkeys(concepts_of_interest, None)
        for concept in concepts_of_interest:
            company_fin_df = pd.DataFrame.from_dict(data_dict['facts']['us-gaap'][concept]['units']['USD'])
            concept_dict[concept] = company_fin_df.loc[company_fin_df['form'] == "10-K", ['end','val']].drop_duplicates().drop_duplicates(subset=['end'], keep='first')
            concept_dict[concept]['end'] = pd.to_datetime(concept_dict[concept]['end'])
        company_facts_df = pd.concat(concept_dict, axis=0)
        company_facts_df.reset_index(inplace=True) 
        company_facts_df.drop(columns=['level_1'], inplace=True)
        company_facts_df.rename(columns = {'level_0':'concept'}, inplace=True)
        all_companies_dict[company] = company_facts_df

    return(all_companies_dict)