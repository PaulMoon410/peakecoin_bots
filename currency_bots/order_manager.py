"""
Centralized order management logic for all bots.
Handles profit enforcement, open order limits, cancellations, self-buy, and profit currency logic.
"""
import time
from currency_bots.place_order import place_order, get_open_orders, cancel_order, get_balance
from currency_bots.profit_strategies import choose_sell_price, scalping_strategy, get_profit_percent

ORDER_LIMIT = 190
ORDERS_TO_CANCEL = 5
MIN_ORDERS_PER_CYCLE = 4

PROFIT_CURRENCIES = ["SWAP.HBD", "SWAP.USDT", "PEK", "SWAP.DOGE", "SWAP.MATIC"]

def enforce_open_order_limit(username, token, active_key=None):
    open_orders = get_open_orders(username)
    if len(open_orders) >= ORDER_LIMIT:
        # Cancel 5 oldest orders
        to_cancel = sorted(open_orders, key=lambda o: o.get('timestamp', 0))[:ORDERS_TO_CANCEL]
        for order in to_cancel:
            cancel_order(username, order['orderId'], active_key=active_key)
            time.sleep(1)
        print(f"[ORDER_MANAGER] Cancelled {len(to_cancel)} oldest orders for {username}")

def cancel_oldest_order(username, active_key=None):
    open_orders = get_open_orders(username)
    if open_orders:
        oldest = min(open_orders, key=lambda o: o.get('timestamp', 0))
        cancel_order(username, oldest['orderId'], active_key=active_key)
        print(f"[ORDER_MANAGER] Cancelled oldest order {oldest['orderId']} for {username}")

def place_profitable_order(username, token, price, qty, order_type, profit_target, scalping_enabled=False, active_key=None):
    # Only place order if it meets profit requirements
    if order_type == "sell":
        min_price = choose_sell_price(price, price, profit_target) if not scalping_enabled else scalping_strategy(price, price)
        if price < min_price:
            print(f"[ORDER_MANAGER] Sell price {price} below profit target {min_price}. Skipping.")
            return False
    # For buys, assume profit is enforced elsewhere (e.g., by sell logic)
    return place_order(username, token, price, qty, order_type=order_type, active_key=active_key)

def ensure_min_orders_per_cycle(username, token, orders_placed, min_orders=MIN_ORDERS_PER_CYCLE, active_key=None):
    # Dummy logic: just print for now
    if orders_placed < min_orders:
        print(f"[ORDER_MANAGER] Only {orders_placed} orders placed, should place at least {min_orders}.")
    # Actual logic to place more orders can be added here

def handle_self_buy(username, token, ask_price, qty, enabled, active_key=None):
    if enabled:
        place_order(username, token, ask_price, qty, order_type="buy", active_key=active_key)
        print(f"[ORDER_MANAGER] Self-buy: {qty} {token} at {ask_price}")

def handle_profit_currency_buy(username, profit_token, price, qty, enabled, active_key=None):
    if enabled and profit_token in PROFIT_CURRENCIES:
        place_order(username, profit_token, price, qty, order_type="buy", active_key=active_key)
        print(f"[ORDER_MANAGER] Profit currency buy: {qty} {profit_token} at {price}")
