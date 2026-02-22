def calculate_min_sell_price(buy_price, min_profit_percent=0.02):
    """Calculate the minimum sell price to achieve desired profit percent (default 2%)."""
    return round(buy_price * (1 + min_profit_percent), 8)

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
