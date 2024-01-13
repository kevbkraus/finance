import requests
import json
import pandas as pd

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
    return cik_list