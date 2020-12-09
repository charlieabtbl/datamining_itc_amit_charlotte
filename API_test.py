import requests

def extract_info_API(company_name):
    """ The function takes the company_name as a parameter and returns information from the Stock Exchange
    platform regarding the stock price, market capitalization, currency and website of the company """

    # Extracting the symbol from the company name
    API_URL_SYMBOL = 'https://stock-exchange-dot-full-stack-course-services.ew.r.appspot.com/api/v3/search'
    parameters = {'query': company_name,
                  'limit': '1', 'exchange': 'NASDAQ'}

    response_symbol = requests.get(API_URL_SYMBOL, params=parameters)
    response_json_symbol = response_symbol.json()
    symbol = response_json_symbol[0]['symbol']

    # Extracting the company_info from the symbol
    API_URL_COMP_INFO = 'https://stock-exchange-dot-full-stack-course-services.ew.r.appspot.com/api/v3/profile/'+str(symbol)

    response_comp = requests.get(API_URL_COMP_INFO)
    response_json_comp = response_comp.json()
    stock_price = response_json_comp[0]['price']
    market_cap = response_json_comp[0]['mktCap']
    currency = response_json_comp[0]['currency']
    website = response_json_comp[0]['website']
    return (stock_price, market_cap, currency, website)

print(extract_info_API('Apple'))