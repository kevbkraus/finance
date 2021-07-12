# valuation_crawler.py ---------------------------------------------------------------------------------------------
#   Crawls through list of U.S. public companies to carry out fundamental valuation and store the results for later
# sorting and selection of companies for manual re-valuation
# ------------------------------------------------------------------------------------------------------------------

from dcf_valuation import get_statements, get_fundamentals, value_company

symbol = 'AAPL'
industry = 'Computers/Peripherals'
response = get_statements(symbol)
response = get_fundamentals(symbol)
response = value_company(symbol, industry, response['fundamentals'])
print('\nFUNDAMENTALS')
print(response['fundamentals'].to_markdown())
