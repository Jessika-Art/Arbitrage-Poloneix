
''' A R B I T R A G E   O N   P O L O N E I X   E X C H A N G E '''
''' Exchange: https://docs.poloniex.com/#introduction '''

''' L I B R A R I E S '''
import json
from pip._vendor import requests
import func_arbitrage
import time


''' ENDPOINT DATA '''
coin_price_url = "https://poloniex.com/public?command=returnTicker"
'''
    Finding coins which can be used.
    Exchange: Poloniex,
    https://docs.poloniex.com/#introduction
'''


''' STEP 0: Get the coins '''
def step_0():
    # Extract a list of coins and prices from the Exchange
    coin_json = func_arbitrage.get_coin_tickers(coin_price_url) # json_obj

    # Loop though each object and find the tradable pairs.
    coin_list = func_arbitrage.collect_tradeables(coin_json)

    # Return a list of tradable coins
    return coin_list

''' STEP 1: Structure Triangular Pairs - Calculation Only '''
def step_1(coin_list):
    # Structure the list of tradable triangular list pairs
    structured_list = func_arbitrage.structure_triangular_pairs(coin_list)

    # Save structure list
    with open('structured triangular_pairs.json', 'w') as fp:
        json.dump(structured_list, fp)
        

''' STEP 2: Calculate Arbitrage Opportunities '''
def step_2():
    # Get structured pairs quickly
    with open("structured triangular_pairs.json") as json_file:
        structured_pairs = json.load(json_file)

    # Get latest surface prices
    prices_json = func_arbitrage.get_coin_tickers(coin_price_url)
    
    # Loop through and Get prices infomation
    for t_pair in structured_pairs:
        time.sleep(0.3)
        prices_dict = func_arbitrage.get_price_for_t_pair(t_pair, prices_json)
        surface_arb = func_arbitrage.calc_triangular_arb_surface_rate(t_pair, prices_dict)
        
        if len(surface_arb) > 0:
            real_rate_arb = func_arbitrage.get_depth_from_orderbook(surface_arb)
            print(real_rate_arb)
            time.sleep(1.2)


''' RUN MAIN '''
# First:
#   Run the 'coin_list = step_0()' and 'structured_pairs = step_1(coin_list)' to collect the data.
# Second:
#   Run the 'step_2()' to see the arbitrages.
if __name__ == '__main__':
    coin_list = step_0()
    structured_pairs = step_1(coin_list)
    # step_2()
    
''' SCHEMA:
1 - Get data, keep only the symbols coin like BTC, ETH, USDT, etc... 

2 - Clean the data cutting off all the double coins I've got.
    Start structuring teh data like this: "BTC_USDT" mark teh first coin "BTC"
    as base and the second one "USDT" as quote, then divide them and 
    make another pair with others bases and quotes.

3 - Put them all together in lists and dictionaries so will be easy to display and work with. 
4 - Make the conditions to calculate the depth of each possible profitable swap. '''
