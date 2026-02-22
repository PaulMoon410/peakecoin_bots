import time
import json as jsonlib
import requests
import os
import math

_last_tx_time = 0
_TX_MIN_DELAY = 10  # seconds

def _enforce_tx_delay():
    global _last_tx_time
    now = time.time()
    elapsed = now - _last_tx_time
    if elapsed < _TX_MIN_DELAY:
        time.sleep(_TX_MIN_DELAY - elapsed)
    _last_tx_time = time.time()

def get_hive_instance(posting_key=None, active_key=None, nodes=None):
    """Return a Hive instance for the given keys and nodes."""
    from beem import Hive
    if nodes is None:
        nodes = ["https://api.hive.blog", "https://anyx.io"]
    keys = []
    if posting_key:
        keys.append(posting_key)
    if active_key:
        keys.append(active_key)
    return Hive(node=nodes, keys=keys)

def get_account_instance(account_name, hive_instance):
    from beem.account import Account
    return Account(account_name, blockchain_instance=hive_instance)

def validate_order_payload(token, quantity, price):
    """Ensure decimals and min order size are correct for token (esp. SWAP.USDT)."""
    if token == "SWAP.USDT":
        min_qty = 0.01
        quantity = max(float(quantity), min_qty)
        quantity = round(quantity, 2)
        price = round(price, 6)
    else:
        quantity = round(float(quantity), 8)
        price = round(price, 6)
    return str(quantity), str(price)

def get_balance(account_name, token):
    payload = {
        "jsonrpc": "2.0",
        "method": "find",
        "params": {
            "contract": "tokens",
            "table": "balances",
            "query": {"account": account_name, "symbol": token},
        },
        "id": 1,
    }
    r = requests.post("https://api.hive-engine.com/rpc/contracts", json=payload)
    if r.status_code == 200:
        result = r.json()
        if result["result"]:
            return float(result["result"][0]["balance"])
    # ...existing code...
    return 0.0

def get_open_orders(account_name, token=None, nodes=None):
    """
    Fetch all open orders for the given account from the openOrders table (across all tokens if token is None).
    Returns a list of orders with 'orderId' field required for cancellation.
    """
    import requests
    if nodes is None:
        nodes = [
            "https://api.hive-engine.com/rpc/contracts",
            "https://herpc.dtools.dev",
            "https://engine.rishipanthee.com/rpc",
            "https://api2.hive-engine.com/rpc/contracts",
        ]
    all_orders = []
    for node in nodes:
        try:
            offset = 0
            page_size = 1000
            while True:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "find",
                    "params": {
                        "contract": "market",
                        "table": "openOrders",
                        "query": {"account": account_name},
                        "limit": page_size,
                        "offset": offset
                    },
                    "id": 1
                }
                if token:
                    payload["params"]["query"]["symbol"] = token
                resp = requests.post(node, json=payload, timeout=10)
                # ...existing code...
                if resp.status_code != 200:
                    break
                data = resp.json()
                orders = data.get('result', [])
                if not isinstance(orders, list):
                    orders = []
                all_orders.extend(orders)
                if len(orders) < page_size:
                    break
                offset += page_size
            if all_orders:
                break  # Use the first working node with results
        except Exception as e:
            # ...existing code...
            continue
    # ...existing code...
    return all_orders

def cancel_order(account_name, order_id, verbose=True, nodes=None, posting_key=None, active_key=None):
    """Cancel an order by its orderId. Returns (success, txid, error). Tries multiple nodes if provided."""
    from beem import Hive
    from beem.transactionbuilder import TransactionBuilder
    from beembase.operations import Custom_json
    import json as jsonlib
    if nodes is None:
        nodes = [
            "https://api.hive.blog",
            "https://anyx.io",
            "https://api.openhive.network",
        ]
    payload = {
        "contractName": "market",
        "contractAction": "cancel",
        "contractPayload": {"orderId": str(order_id)},
    }
    for node in nodes:
        try:
            hive = Hive(node=node, keys=[k for k in [posting_key, active_key] if k])
            tx = TransactionBuilder(blockchain_instance=hive)
            # IMPORTANT: For Hive-Engine order cancellation, required_posting_auths must be [] and required_auths must include the account name (active key required).
            op = Custom_json(
                required_auths=[account_name],
                required_posting_auths=[],
                id="ssc-mainnet-hive",
                json=jsonlib.dumps(payload),
            )
            # ...existing code...
            tx.appendOps([op])
            tx.appendSigner(account_name, "active")
            tx.sign()
            broadcast_result = tx.broadcast()
            # ...existing code...
            tx_id = None
            if isinstance(broadcast_result, dict):
                tx_id = (
                    broadcast_result.get('id') or
                    broadcast_result.get('txid') or
                    broadcast_result.get('transaction_id') or
                    (broadcast_result.get('result') and (
                        broadcast_result['result'].get('id') or
                        broadcast_result['result'].get('txid') or
                        broadcast_result['result'].get('transaction_id')
                    ))
                )
            if isinstance(broadcast_result, dict) and broadcast_result.get('error'):
                error_msg = broadcast_result['error']
                continue  # Try next node
            return (True, tx_id, None)
        except Exception as e:
            # ...existing code...
            continue  # Try next node
    return (False, None, 'All nodes failed to broadcast cancel order')

def build_and_send_op(account_name, symbol, price, quantity, order_type, posting_key=None, active_key=None, nodes=None):
    from beem.transactionbuilder import TransactionBuilder
    from beembase.operations import Custom_json
    from beem.instance import set_shared_blockchain_instance
    hive = get_hive_instance(posting_key, active_key, nodes)
    set_shared_blockchain_instance(hive)
    # Validate decimals and min order size
    quantity, price = validate_order_payload(symbol, quantity, price)
    payload = {
        "contractName": "market",
        "contractAction": order_type,
        "contractPayload": {
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
        },
    }
    # ...existing code...
    tx = TransactionBuilder(blockchain_instance=hive)
    op = Custom_json(
        required_auths=[account_name],
        required_posting_auths=[],
        id="ssc-mainnet-hive",
        json=jsonlib.dumps(payload),
    )
    tx.appendOps([op])
    tx.appendSigner(account_name, "active")
    try:
        tx.sign()
        broadcast_result = tx.broadcast()
        tx_id = None
        if isinstance(broadcast_result, dict):
            tx_id = (
                broadcast_result.get('id') or
                broadcast_result.get('txid') or
                broadcast_result.get('transaction_id') or
                (broadcast_result.get('result') and (
                    broadcast_result['result'].get('id') or
                    broadcast_result['result'].get('txid') or
                    broadcast_result['result'].get('transaction_id')
                ))
            )
        # ...existing code...
        return tx_id
    except Exception:
        return None

def place_order(account_name, token, price, quantity, order_type="buy", posting_key=None, active_key=None, nodes=None):
    _enforce_tx_delay()
    """Generic, safe order placement for any account/keys/nodes."""
    # Use env vars as fallback if not provided
    posting_key = posting_key or os.environ.get("HIVE_POSTING_KEY")
    active_key = active_key or os.environ.get("HIVE_ACTIVE_KEY")
    nodes = nodes or ["https://api.hive.blog", "https://anyx.io"]
    if account_name in {"strangedad", "peakecoin.bnb"} and token.upper() == "SWAP.BCH" and order_type == "buy":
        print(f"[ORDER] Blocked SWAP.BCH buy for {account_name}.")
        return False
    # ...existing code...
    # Use SWAP.HIVE as the base token for all buy orders
    token_used = "SWAP.HIVE" if order_type == "buy" else token
    available = get_balance(account_name, token_used)
    # ...existing code...
    if available < quantity:
        quantity = max(available * 0.95, 0.00001)
    if quantity <= 0:
        return False
    try:
        tx_id = build_and_send_op(account_name, token, price, quantity, order_type, posting_key, active_key, nodes)
        return True if tx_id else False
    except Exception:
        return False

# Default gas settings (can be changed in one place for all bots)
DEFAULT_GAS_TOKEN = "SWAP.MATIC"
DEFAULT_GAS_AMOUNT = 0.01
DEFAULT_GAS_PRICE = 1.0  # Set a reasonable default, can be overridden

def buy_gas(account_name, gas_token=None, gas_amount=None, gas_price=None, posting_key=None, active_key=None, nodes=None):
    _enforce_tx_delay()
    """Generic function to buy gas (any token) for the account. Uses defaults if not specified."""
    token = gas_token if gas_token is not None else DEFAULT_GAS_TOKEN
    amount = gas_amount if gas_amount is not None else DEFAULT_GAS_AMOUNT
    price = gas_price if gas_price is not None else DEFAULT_GAS_PRICE
    # ...existing code...
    return place_order(
        account_name,
        token,
        price,
        amount,
        order_type="buy",
        posting_key=posting_key,
        active_key=active_key,
        nodes=nodes,
    )


PEAKECOIN_GAS_TOKEN = "PEK"
PEAKECOIN_GAS_AMOUNT = 1
PEAKECOIN_GAS_PRICE = 0.000001
PEAKECOIN_GAS_OFFSET = 62  # e.g. 1m2s offset from start
PEAKECOIN_GAS_INTERVAL = 3600  # every hour

def buy_peakecoin_gas(account_name, posting_key=None, active_key=None, nodes=None):
    _enforce_tx_delay()
    """Place a PEK buy order at 0.000001 HIVE for 1 PEK, offset from other gas buys."""
    # ...existing code...
    return place_order(
        account_name,
        PEAKECOIN_GAS_TOKEN,
        PEAKECOIN_GAS_PRICE,
        PEAKECOIN_GAS_AMOUNT,
        order_type="buy",
        posting_key=posting_key,
        active_key=active_key,
        nodes=nodes,
    )

def next_peakecoin_gas_time(start_time, interval=PEAKECOIN_GAS_INTERVAL, offset=PEAKECOIN_GAS_OFFSET):
    """Return the next PEK gas buy time (epoch seconds), offset by 'offset' seconds from start, then every 'interval' seconds after."""
    now = time.time()
    if now < start_time + offset:
        return start_time + offset
    cycles = math.ceil((now - (start_time + offset)) / interval)
    return start_time + offset + cycles * interval

def should_buy_peakecoin_gas(last_gas_time, interval=PEAKECOIN_GAS_INTERVAL, offset=PEAKECOIN_GAS_OFFSET):
    """Return True if it's time to buy PEK gas (offset from start by 'offset', then every 'interval')."""
    now = time.time()
    if last_gas_time == 0:
        return now >= (now // interval) * interval + offset
    return now - last_gas_time >= interval

def next_gas_time(start_time, interval=3600, offset=20):
    """Return the next gas buy time (epoch seconds), offset by 'offset' seconds from start, then every 'interval' seconds after."""
    now = time.time()
    if now < start_time + offset:
        return start_time + offset
    cycles = math.ceil((now - (start_time + offset)) / interval)
    return start_time + offset + cycles * interval

def should_buy_gas(last_gas_time, interval=3600, offset=20):
    """Return True if it's time to buy gas (offset from start by 'offset', then every 'interval')."""
    now = time.time()
    if last_gas_time == 0:
        return now >= (now // interval) * interval + offset
    return now - last_gas_time >= interval

def get_hive_posting_key():
    """Return the Hive posting key from environment variable."""
    return os.environ.get("HIVE_POSTING_KEY")

__all__ = [
    'place_order', 'get_open_orders', 'cancel_order', 'get_balance',
    'buy_gas', 'should_buy_gas', 'buy_peakecoin_gas', 'should_buy_peakecoin_gas',
]
