def calculate_min_sell_price(buy_price, min_profit_percent=0.02):
    """Calculate the minimum sell price to achieve desired profit percent (default 2%)."""
    return round(buy_price * (1 + min_profit_percent), 8)

def choose_sell_price(buy_price, market_sell_price, profit_target_percent=2.0, precision=8):
    """Return a sell price that respects the minimum profit target while using market price when favorable."""
    if buy_price <= 0:
        return 0.0

    min_profit_percent = max(float(profit_target_percent), 0.0) / 100
    min_sell_price = calculate_min_sell_price(buy_price, min_profit_percent)

    if market_sell_price > 0 and is_profitable(buy_price, market_sell_price, min_profit_percent):
        return round(market_sell_price, precision)

    return round(min_sell_price, precision)

def is_profitable(buy_price, sell_price, min_profit_percent=0.02):
    """
    Return True if sell_price meets or exceeds the minimum profit percent over buy_price.
    Guarantees profit if True.
    """
    min_sell = calculate_min_sell_price(buy_price, min_profit_percent)
    return sell_price >= min_sell

def is_profitable_or_volume_increase(buy_price, sell_price, buy_qty, sell_qty, min_profit_percent=0.02):
    """
    Return True if and only if sell_price meets/exceeds minimum profit percent over buy_price.
    Guarantees profit on every sale.
    """
    min_sell = calculate_min_sell_price(buy_price, min_profit_percent)
    return sell_price >= min_sell

def get_profit_percent(buy_price, sell_price):
    """Return the actual profit percent for a given buy/sell price."""
    if buy_price == 0:
        return 0.0
    return round((sell_price - buy_price) / buy_price * 100, 4)
