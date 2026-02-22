import requests

def get_orderbook_top(token="SWAP.LTC"):
    # Pull top buy orders (usually works correctly with sorting)
    buy_payload = {
        "jsonrpc": "2.0",
        "method": "find",
        "params": {
            "contract": "market",
            "table": "buyBook",
            "query": {"symbol": token},
            "limit": 1000,
            "indexes": [{"index": "priceDec", "descending": True}]
        },
        "id": 1
    }

    # Pull up to 1000 sell orders to ensure we capture the true lowest ask
    sell_payload = {
        "jsonrpc": "2.0",
        "method": "find",
        "params": {
            "contract": "market",
            "table": "sellBook",
            "query": {"symbol": token},
            "limit": 1000,
            "indexes": [{"index": "price", "descending": False}]
        },
        "id": 2
    }

    # Request both buy and sell books
    buy_response = requests.post("https://api.hive-engine.com/rpc/contracts", json=buy_payload)
    sell_response = requests.post("https://api.hive-engine.com/rpc/contracts", json=sell_payload)

    if buy_response.status_code == 200 and sell_response.status_code == 200:
        buy_result = buy_response.json().get("result", [])
        sell_result = sell_response.json().get("result", [])

        # Use the highest priced buy order (top bid)
        highest_bid = float(buy_result[0]["price"]) if buy_result else 0

        # Use the true lowest sell price found in the result
        valid_asks = [float(order["price"]) for order in sell_result if float(order["price"]) > 0]
        lowest_ask = min(valid_asks) if valid_asks else 0

        return {"highestBid": highest_bid, "lowestAsk": lowest_ask}

    return None

def get_account_open_orders(account, limit=1000):
    """
    Fetch all open orders for the given account (across all tokens), paginated if needed.
    Returns a list of all open orders.
    """
    url = "https://api.hive-engine.com/rpc/contracts"
    all_orders = []
    offset = 0
    page_size = limit
    while True:
        payload = {
            "jsonrpc": "2.0",
            "method": "find",
            "params": {
                "contract": "market",
                "table": "openOrders",
                "query": {"account": account},
                "limit": page_size,
                "offset": offset
            },
            "id": 1
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch open orders for {account} (status {resp.status_code})")
            break
        data = resp.json()
        orders = data.get('result')
        if not isinstance(orders, list):
            orders = []
        all_orders.extend(orders)
        if len(orders) < page_size:
            break
        offset += page_size
    return all_orders

def get_account_open_orders_all_tokens(account, limit=1000):
    """
    Fetch all open orders for the given account (across all tokens), paginated if needed.
    Returns a list of all open orders (all tokens).
    """
    url = "https://api.hive-engine.com/rpc/contracts"
    all_orders = []
    offset = 0
    page_size = limit
    while True:
        payload = {
            "jsonrpc": "2.0",
            "method": "find",
            "params": {
                "contract": "market",
                "table": "openOrders",
                "query": {"account": account},
                "limit": page_size,
                "offset": offset
            },
            "id": 1
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[ERROR] Failed to fetch open orders for {account} (status {resp.status_code})")
            break
        data = resp.json()
        orders = data.get('result')
        if not isinstance(orders, list):
            orders = []
        all_orders.extend(orders)
        if len(orders) < page_size:
            break
        offset += page_size
    return all_orders
