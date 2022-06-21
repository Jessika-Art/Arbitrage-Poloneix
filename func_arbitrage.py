
from pip._vendor import requests
import json
import time

# Make a get request
def get_coin_tickers(url):
    req = requests.get(url)
    json_resp = json.loads(req.text)
    return json_resp

# Loop through each objects and find the tradeable pairs
def collect_tradeables(json_obj):
    global coin_list
    coin_list = []
    for coin in json_obj:
        is_frozen = json_obj[coin]["isFrozen"]
        is_post_only = json_obj[coin]["postOnly"]
        if is_frozen == "0" and is_post_only == "0":
            coin_list.append(coin)
    print(coin_list)
    return coin_list

# Structure Arbitrage Pairs
def structure_triangular_pairs(coin_list):

    # Declare Variables
    triangular_pairs_list = []
    remove_duplicates_list = []
    pairs_list = coin_list[0:]

    # Get Pair A
    for pair_a in pairs_list:
        pair_a_split = pair_a.split("_")
        a_base = pair_a_split[0]
        a_quote = pair_a_split[1]

        # Assign A to a Box
        a_pair_box = [a_base, a_quote]

        # Get Pair B
        for pair_b in pairs_list:
            pair_b_split = pair_b.split("_")
            b_base = pair_b_split[0]
            b_quote = pair_b_split[1]

            # Check Pair B
            if pair_b != pair_a:
                if b_base in a_pair_box or b_quote in a_pair_box:

                    # Get Pair C
                    for pair_c in pairs_list:
                        pair_c_split = pair_c.split("_")
                        c_base = pair_c_split[0]
                        c_quote = pair_c_split[1]

                        # Count the number of matching C items
                        if pair_c != pair_a and pair_c != pair_b:
                            combine_all = [pair_a, pair_b, pair_c]
                            pair_box = [a_base, a_quote, b_base, b_quote, c_base, c_quote]

                            counts_c_base = 0
                            for i in pair_box:
                                if i == c_base:
                                    counts_c_base += 1

                            counts_c_quote = 0
                            for i in pair_box:
                                if i == c_quote:
                                    counts_c_quote += 1

                            # Determining Triangular Match
                            if counts_c_base == 2 and counts_c_quote == 2 and c_base != c_quote:
                                combined = f'{pair_a}, {pair_b}, {pair_c}'
                                unique_item = ''.join(sorted(combine_all)) # sort in order 

                                if unique_item not in remove_duplicates_list:
                                    match_dict = {
                                        'a_base': a_base,
                                        'b_base': b_base,
                                        'c_base': c_base,
                                        'a_quote': a_quote,
                                        'b_quote': b_quote,
                                        'c_quote': c_quote,
                                        'pair_a': pair_a,
                                        'pair_b': pair_b,
                                        'pair_c': pair_c,
                                        'combined': combined
                                    }
                                    triangular_pairs_list.append(match_dict)
                                    remove_duplicates_list.append(unique_item)
    return triangular_pairs_list   
                                    
# Structured Prices
def get_price_for_t_pair(t_pair, prices_json):
    # Extract pair info
    pair_a = t_pair['pair_a']
    pair_b = t_pair['pair_b']
    pair_c = t_pair['pair_c']
    
    # Extract prices info for given pairs
    pair_a_ask = float(prices_json[pair_a]['lowestAsk'])
    pair_a_bid = float(prices_json[pair_a]['highestBid'])
    pair_b_ask = float(prices_json[pair_b]['lowestAsk'])
    pair_b_bid = float(prices_json[pair_b]['highestBid'])
    pair_c_ask = float(prices_json[pair_c]['lowestAsk'])
    pair_c_bid = float(prices_json[pair_c]['highestBid'])

    # Output dictionaty
    return {
        'pair_a_ask': pair_a_ask,
        'pair_a_bid': pair_a_bid,
        'pair_b_ask': pair_b_ask,
        'pair_b_bid': pair_b_bid,
        'pair_c_ask': pair_c_ask,
        'pair_c_bid': pair_c_bid,
    }
   
# Calculate Surface Rate Arbitrage Opportunity
def calc_triangular_arb_surface_rate(t_pair, prices_dict):

    # Set variables
    starting_amount = 100 # tha initial capital: if it is BTC/ETH I'll have 1 BTC, if it is USDT/ETH I'll have 1 USDT, always takes the first symbol.
    #mim_surface_rate = 0.5 # this variable is set to 0, so it gives me all the arbitrage with NO loss, only profit.

    surface_dict = {}
    contract_2 = ''
    contract_3 = ''
    direction_trade_1 = ''
    direction_trade_2 = ''
    direction_trade_3 = ''
    acquired_coin_t2 = 0
    acquired_coin_t3 = 0
    calculated = 0

    # Extract pair variables
    a_base = t_pair['a_base']
    a_quote = t_pair['a_quote']
    b_base = t_pair['b_base']
    b_quote = t_pair['b_quote']
    c_base = t_pair['c_base']
    c_quote = t_pair['c_quote']

    pair_a = t_pair['pair_a']
    pair_b = t_pair['pair_b']
    pair_c = t_pair['pair_c']

    # Extract price information
    a_ask = prices_dict['pair_a_ask']
    a_bid = prices_dict['pair_a_bid']
    b_ask = prices_dict['pair_b_ask']
    b_bid = prices_dict['pair_b_bid']
    c_ask = prices_dict['pair_c_ask']
    c_bid = prices_dict['pair_c_bid']

    # Set directions and loop through
    direction_list = ['forward', 'reverse']
    for direction in direction_list:
        # Set additional variables for swap information
        swap_1 = 0
        swap_2 = 0
        swap_3 = 0
        swap_1_rate = 0
        swap_2_rate = 0
        swap_3_rate = 0

        '''
            Poloniex Rules !
            if I'm swapping the coin from the left(Base) to the right(Quote), then * (1 / Ask)
            if I'm swapping the coin from the right(Quote) to the left(Base), then * Bid
        '''

        # Assume starting with a_base swapping to a_quote
        if direction == 'forward':
            swap_1 = a_base
            swap_2 = a_quote
            swap_1_rate = 1 / a_ask
            direction_trade_1 = 'base_to_quote'

        if direction == 'reverse':
            swap_1 = a_quote
            swap_2 = a_base
            swap_1_rate = a_bid
            direction_trade_1 = 'quote_to_base'
           
        # Place first trade
        contract_1 = pair_a
        acquired_coin_t1 = starting_amount * swap_1_rate
        
        ''' FORWARD '''
        # SCENARIO 1: Check if a_quote (acquired_coin) matches b_quote
        if direction == 'forward':
            if a_quote == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'quote_to_base'
                contract_2 = pair_b

                # if b_base(acquired) matches c_base
                if  b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_c

                # if b_base(acquired) matches c_quote
                if  b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_c
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 2:Check if a_quote (acquired_coin) matches b_base
        if direction == 'forward':
            if a_quote == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'base_to_quote'
                contract_2 = pair_b

                # if b_quote(acquired) matches c_base
                if  b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_c

                # if b_quote(acquired) matches c_quote
                if  b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_c
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 3: Check if a_quote (acquired_coin) matches b_quote
        if direction == 'forward':
            if a_quote == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'quote_to_base'
                contract_2 = pair_c

                # if c_base(acquired) matches b_base
                if  c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_b

                # if c_base(acquired) matches b_quote
                if  c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_b
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 4:Check if a_quote (acquired_coin) matches c_base
        if direction == 'forward':
            if a_quote == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'base_to_quote'
                contract_2 = pair_c

                # if c_quote(acquired) matches b_base
                if  c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_b

                # if c_quote(acquired) matches b_quote
                if  c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_b
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1


        ''' REVERSE '''
        # SCENARIO 1: Check if a_base (acquired_coin) matches b_quote
        if direction == 'reverse':
            if a_base == b_quote and calculated == 0:
                swap_2_rate = b_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'quote_to_base'
                contract_2 = pair_b

                # if b_base(acquired) matches c_base
                if  b_base == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_c

                # if b_base(acquired) matches c_quote
                if  b_base == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_c
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 2:Check if a_base (acquired_coin) matches b_base
        if direction == 'reverse':
            if a_base == b_base and calculated == 0:
                swap_2_rate = 1 / b_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'base_to_quote'
                contract_2 = pair_b

                # if b_quote(acquired) matches c_base
                if  b_quote == c_base:
                    swap_3 = c_base
                    swap_3_rate = 1 / c_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_c

                # if b_quote(acquired) matches c_quote
                if  b_quote == c_quote:
                    swap_3 = c_quote
                    swap_3_rate = c_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_c
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 3: Check if a_base (acquired_coin) matches b_quote
        if direction == 'reverse':
            if a_base == c_quote and calculated == 0:
                swap_2_rate = c_bid
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'quote_to_base'
                contract_2 = pair_c

                # if c_base(acquired) matches b_base
                if  c_base == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_b

                # if c_base(acquired) matches b_quote
                if  c_base == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_b
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1

        # SCENARIO 4:Check if a_base (acquired_coin) matches c_base
        if direction == 'reverse':
            if a_base == c_base and calculated == 0:
                swap_2_rate = 1 / c_ask
                acquired_coin_t2 = acquired_coin_t1 * swap_2_rate
                direction_trade_2 = 'base_to_quote'
                contract_2 = pair_c

                # if c_quote(acquired) matches b_base
                if  c_quote == b_base:
                    swap_3 = b_base
                    swap_3_rate = 1 / b_ask
                    direction_trade_3 = 'base_to_quote'
                    contract_3 = pair_b

                # if c_quote(acquired) matches b_quote
                if  c_quote == b_quote:
                    swap_3 = b_quote
                    swap_3_rate = b_bid 
                    direction_trade_3 = 'quote_to_base'
                    contract_3 = pair_b
                
                acquired_coin_t3 = acquired_coin_t2 * swap_3_rate
                calculated = 1
        

        ''' PROFIT LOSS OUTPUT '''

        # Profit and Loss calculations
        profit_loss = acquired_coin_t3 - starting_amount
        profit_loss_perc = (profit_loss / starting_amount) * 100 if profit_loss != 0 else 0 # this 'if' prevet to get as a result 0.

        # Trade descriptions
        trade_description_1 = f'S T A R T with capital: {starting_amount} >{swap_1}. Swap at {swap_1_rate} for {swap_2} acquiring the coin amout of: {acquired_coin_t1} >{swap_2}.'
        trade_description_2 = f'S W A P {acquired_coin_t1} >{swap_2} at {swap_2_rate} for {swap_3} acquiring the coin amount of: {acquired_coin_t2} >{swap_3}.'
        trade_description_3 = f'S W A P {acquired_coin_t2} >{swap_3} at {swap_3_rate} for {swap_1} returning the coin amout of: {acquired_coin_t3} >{swap_1} TOT WON {profit_loss_perc}.\/\/\/\/\/\/\/\/\/\/\/\/\/'

        ''' INCREASE OR DECREASE THE DIFFERENCE BETWEEN EACH SWAP '''
        if profit_loss > 0:
            print(f'NEW TRADE === {profit_loss_perc}')
            print(direction, direction_trade_1, direction_trade_2, direction_trade_3)
            print(pair_a, pair_b, pair_c)
            print(trade_description_1)
            print(trade_description_2)
            print(trade_description_3)

        ''' SEE THE PROFITABLE SWAPS '''
        # Output Results
        if profit_loss_perc > 0:
            surface_dict = {
                "swap_1": swap_1,
                "swap_2": swap_2,
                "swap_3": swap_3,
                "contract_1": contract_1,
                "contract_2": contract_2,
                "contract_3": contract_3,
                "direction_trade_1": direction_trade_1,
                "direction_trade_2": direction_trade_2,
                "direction_trade_3": direction_trade_3,
                "starting_amount": starting_amount,
                "acquired_coin_t1": acquired_coin_t1,
                "acquired_coin_t2": acquired_coin_t2,
                "acquired_coin_t3": acquired_coin_t3,
                "swap_1_rate": swap_1_rate,
                "swap_2_rate": swap_2_rate,
                "swap_3_rate": swap_3_rate,
                "profit_loss": profit_loss,

                "profit_loss_perc": profit_loss_perc,
                "direction": direction,
                "trade_description_1": trade_description_1,
                "trade_description_2": trade_description_2,
                "trade_description_3": trade_description_3
            }

            return surface_dict

    return surface_dict
            
# Reformat Order Book for depth Calculation
def reformatted_orderbook(prices, c_direction):
    price_list_main = []
    if c_direction == 'base_to_quote':
        for p in prices['asks']:
            ask_price = float(p[0])
            adj_price = 1 / ask_price if ask_price != 0 else 0
            adj_quantity = float(p[1]) * ask_price
            price_list_main.append([adj_price, adj_quantity])

    if c_direction == 'quote_to_base':
        for p in prices['bids']:
            bid_price = float(p[0])
            adj_price = bid_price if bid_price != 0 else 0
            adj_quantity = float(p[1])
            price_list_main.append([adj_price, adj_quantity])
    
    return price_list_main

# Get Acqired Coin also known as Depth CAlculation
def calculate_acquired_coin(amount_in, orderbook):
    ''' CHALLENGES 
        Full amount of starting amount in can be eaten on the first lever(level 0) 
        Some of the amount in can be eaten up by multiple levels
        Some coins may not have enough liquidity 
    '''
    
    # Initialise variables
    trading_balance = amount_in
    quantity_bought = 0
    acquired_coin = 0
    counts = 0
    for level in orderbook:
        # Extract the price and the quantity
        level_price = level[0]
        level_available_quantity = level[1]

        # Amount_in is <= first level total amount
        if float(trading_balance) <= float(level_available_quantity):
            quantity_bought = trading_balance
            trading_balance = 0
            amount_bought = quantity_bought * level_price

        # Amount_in is > given level total amount
        if trading_balance > level_available_quantity:
            quantity_bought = level_available_quantity
            trading_balance -= quantity_bought
            amount_bought = quantity_bought * level_price

        # Accumulate acquired coin
        acquired_coin = acquired_coin + amount_bought

        # Extit Trade
        if trading_balance == 0:
            return acquired_coin

        # Exit if not enough order book levels
        counts += 1
        if counts == len(orderbook):
            return ''


# Get the Depth from the Order Book
def get_depth_from_orderbook(surface_arb):
    ''' CHALLENGES 
        Full amount of starting amount in can be eaten on the first lever(level 0) 
        Some of the amount in can be eaten up by multiple levels
        Some coins may not have enough liquidity 
    '''

    # Extract initial variables
    swap_1 = surface_arb['swap_1']
    starting_amount = 100
    starting_amount_dict = {
        'USDT': 100, 
        'USDC': 100, 
        'BTC': 0.005, 
        'ETH': 0.02
        }
    if swap_1 in starting_amount_dict:
        starting_amount = starting_amount_dict[swap_1]

    # Define Pairs
    contract_1 = surface_arb['contract_1']
    contract_2 = surface_arb['contract_2']
    contract_3 = surface_arb['contract_3']

    # Define direction for trade
    contract_1_direction = surface_arb['direction_trade_1']
    contract_2_direction = surface_arb['direction_trade_2']
    contract_3_direction = surface_arb['direction_trade_3']

    # Get Order Book for first Trade Assessment
    url1 = f"https://poloniex.com/public?command=returnOrderBook&currencyPair={contract_1}&depth=50"
    depth_1_prices = get_coin_tickers(url1)
    depth_1_reformatted_prices = reformatted_orderbook(depth_1_prices, contract_1_direction)
    time.sleep(0.3)
    url2 = f"https://poloniex.com/public?command=returnOrderBook&currencyPair={contract_2}&depth=50"
    depth_2_prices = get_coin_tickers(url2)
    depth_2_reformatted_prices = reformatted_orderbook(depth_2_prices, contract_2_direction)
    time.sleep(0.3)
    url3 = f"https://poloniex.com/public?command=returnOrderBook&currencyPair={contract_3}&depth=50"
    depth_3_prices = get_coin_tickers(url3)
    depth_3_reformatted_prices = reformatted_orderbook(depth_3_prices, contract_3_direction)

    # Get Acquired Coins
    acquired_coin_t1 = calculate_acquired_coin(starting_amount, depth_1_reformatted_prices)
    acquired_coin_t2 = calculate_acquired_coin(acquired_coin_t1, depth_2_reformatted_prices)
    acquired_coin_t3 = calculate_acquired_coin(acquired_coin_t2, depth_3_reformatted_prices)

    # Calculate Profit Loss also known as Real Rate
    profit_loss = acquired_coin_t3 - starting_amount
    real_rate_perc = (profit_loss / starting_amount) * 100 if profit_loss != 0 else 0

    if real_rate_perc > 2:
        return_dict = {
            'profit_loss': profit_loss,
            'real_rate_perc': real_rate_perc,
            'contract_1': contract_1,
            'contract_2': contract_2,
            'contract_3': contract_3,
            'contract_1_direction': contract_1_direction,
            'contract_2_direction': contract_2_direction,
            'contract_3_direction': contract_3_direction
        }
        print(return_dict)
    # else:
    #     return {}



