import requests
import logging
import json

logger = logging.getLogger('glassdoor_scraping.log')


def extract_info_API(company_name):
    """ The function takes the company_name as a parameter and returns information from the Stock Exchange
    platform regarding the stock price, market capitalization, currency and website of the company """

    with open('config.json', 'r') as config_file:
        api_params = json.load(config_file)['API']

    # Extracting the symbol from the company name
    api_search = api_params['search']

    stock_markets = ['NYSE', 'NASDAQ', 'AMEX', 'EURONEX', 'TSX',
                     'INDEXES', 'ETFs', 'MUTUAL FUNDS', 'FOREX', 'CRYPTO']

    for market in stock_markets:
        parameters = {'query': company_name,
                      'limit': '1', 'exchange': market}

        response_symbol = requests.get(api_search, params=parameters)
        response_json_symbol = response_symbol.json()

        if len(response_json_symbol):

            try:
                symbol = response_json_symbol[0]['symbol']
            except Exception as e:
                print(e)
                continue

            # Extracting the company_info from the symbol
            api_profile = api_params['profile'] + str(symbol)

            response_comp = requests.get(api_profile)
            response_json_comp = response_comp.json()
            stock_price = response_json_comp[0]['price']
            market_cap = response_json_comp[0]['mktCap']
            currency = response_json_comp[0]['currency']
            website = response_json_comp[0]['website']
            exchange_market = response_json_comp[0]['exchangeShortName']

            return stock_price, market_cap, currency, website, exchange_market
        else:
            return None, None, None, None, None


if __name__ == "__main__":
    print(extract_info_API('Apple'))