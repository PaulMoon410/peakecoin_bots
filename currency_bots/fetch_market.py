import requests

from utils.settings import DEFAULT_ENGINE_NODE, DEFAULT_HIVE_RC_NODE, MIN_RESOURCE_CREDITS

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
    try:
        buy_response = requests.post(DEFAULT_ENGINE_NODE, json=buy_payload, timeout=12)
        sell_response = requests.post(DEFAULT_ENGINE_NODE, json=sell_payload, timeout=12)
    except Exception as exc:
        print(f"[MARKET] Request exception for {token}: {exc}")
        return None

    if buy_response.status_code == 200 and sell_response.status_code == 200:
        try:
            buy_result = buy_response.json().get("result", [])
            sell_result = sell_response.json().get("result", [])
        except Exception as exc:
            print(f"[MARKET] JSON parse error for {token}: {exc}")
            return None

        # Use the highest priced buy order (top bid)
        highest_bid = float(buy_result[0]["price"]) if buy_result else 0

        # Use the true lowest sell price found in the result
        valid_asks = [float(order["price"]) for order in sell_result if float(order["price"]) > 0]
        lowest_ask = min(valid_asks) if valid_asks else 0

        return {"highestBid": highest_bid, "lowestAsk": lowest_ask}

    print(
        f"[MARKET] HTTP failure for {token}: "
        f"buy={buy_response.status_code}, sell={sell_response.status_code}"
    )

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

def get_resource_credits(account_name, node_url=DEFAULT_HIVE_RC_NODE):
    """Return current resource credits percentage for the Hive account."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "rc_api.find_rc_accounts",
            "params": {"accounts": [account_name]},
            "id": 1
        }
        resp = requests.post(node_url, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            rc = data.get("result", {}).get("rc_accounts", [{}])[0]
            if rc and "rc_manabar" in rc and "max_rc" in rc:
                current = int(rc["rc_manabar"]["current_mana"])
                max_rc = int(rc["max_rc"])
                return round(current / max_rc * 100, 2) if max_rc > 0 else 0.0
    except Exception:
        pass
    return None
