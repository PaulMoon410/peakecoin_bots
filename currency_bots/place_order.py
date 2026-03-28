import time
import json as jsonlib
import requests
import os
import math
import sys
import types
import hashlib
import traceback

_last_tx_time = 0
_TX_MIN_DELAY = 10  # seconds


def _ensure_scrypt_compat():
    """Ensure `scrypt` import works in PyInstaller builds.

    Some frozen environments fail importing the binary `scrypt` package with:
    `AttributeError: 'NoneType' object has no attribute 'origin'`.
    In that case, inject a tiny compatible module using `hashlib.scrypt`.
    """
    try:
        import scrypt as _scrypt  # noqa: F401
        return
    except Exception as exc:
        print(f"[ORDER] scrypt import fallback engaged: {exc}")

    shim = types.ModuleType("scrypt")

    def _normalize_bytes(value):
        if isinstance(value, str):
            return value.encode("utf-8")
        return value

    def _hash(password, salt, N=16384, r=8, p=1, buflen=64):
        return hashlib.scrypt(
            _normalize_bytes(password),
            salt=_normalize_bytes(salt),
            n=int(N),
            r=int(r),
            p=int(p),
            maxmem=0,
            dklen=int(buflen),
        )

    shim.hash = _hash
    shim.scrypt = _hash
    sys.modules["scrypt"] = shim
    print("[ORDER] Injected hashlib-based scrypt compatibility module")

def _enforce_tx_delay():
    global _last_tx_time
    now = time.time()
    elapsed = now - _last_tx_time
    if elapsed < _TX_MIN_DELAY:
        wait_for = _TX_MIN_DELAY - elapsed
        print(f"[ORDER] Rate limit delay: waiting {wait_for:.2f}s before next transaction")
        time.sleep(wait_for)
    _last_tx_time = time.time()

def get_hive_instance(posting_key=None, active_key=None, nodes=None):
    """Return a Hive instance for the given keys and nodes."""
    _ensure_scrypt_compat()
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
        price = round(float(price), 8)  # allow sub-1e-6 prices
    else:
        quantity = round(float(quantity), 8)
        price = round(float(price), 8)  # allow sub-1e-6 prices
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
    try:
        r = requests.post("https://api.hive-engine.com/rpc/contracts", json=payload, timeout=12)
    except Exception as exc:
        print(f"[BALANCE] Request exception for {account_name} {token}: {exc}")
        return 0.0
    if r.status_code == 200:
        result = r.json()
        if result["result"]:
            return float(result["result"][0]["balance"])
        print(f"[BALANCE] No balance row for {account_name} {token}; treating as 0")
    else:
        print(f"[BALANCE] HTTP {r.status_code} while fetching {account_name} {token}")
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

def _get_total_open_orders(account_name):
    try:
        orders = get_open_orders(account_name)
        if orders:
            return len(orders)
    except Exception:
        orders = []
    try:
        combined = []
        for node in [
            "https://api.hive-engine.com/rpc/contracts",
            "https://herpc.dtools.dev",
            "https://engine.rishipanthee.com/rpc",
            "https://api2.hive-engine.com/rpc/contracts",
        ]:
            try:
                for table in ("buyBook", "sellBook"):
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "find",
                        "params": {
                            "contract": "market",
                            "table": table,
                            "query": {"account": account_name},
                            "limit": 1000,
                        },
                        "id": 1,
                    }
                    r = requests.post(node, json=payload, timeout=10)
                    if r.status_code == 200:
                        res = r.json().get("result", [])
                        if isinstance(res, list):
                            combined.extend(res)
                if combined:
                    break
            except Exception:
                continue
        return len(combined)
    except Exception:
        return 0

def cancel_order(account_name, order_id, verbose=True, nodes=None, posting_key=None, active_key=None):
    """Cancel an order by its orderId. Returns (success, txid, error). Tries multiple nodes if provided."""
    _ensure_scrypt_compat()
    from beem import Hive
    from beem.transactionbuilder import TransactionBuilder
    from beembase.operations import Custom_json
    import json as jsonlib
    try:
        total_open = _get_total_open_orders(account_name)
        if total_open < 190:
            print(f"[i] Cancel skipped: total open orders {total_open} < 190 for {account_name}.")
            return (False, None, "below-threshold")
    except Exception:
        pass
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
    _ensure_scrypt_compat()
    from beem.transactionbuilder import TransactionBuilder
    from beembase.operations import Custom_json
    from beem.instance import set_shared_blockchain_instance
    hive = get_hive_instance(posting_key, active_key, nodes)
    set_shared_blockchain_instance(hive)
    # Validate decimals and min order size
    quantity, price = validate_order_payload(symbol, quantity, price)
    if account_name in {"strangedad", "peakecoin.bnb"} and symbol.upper() == "SWAP.BCH" and order_type == "buy":
        print(f"[ORDER] Blocked SWAP.BCH buy for {account_name}.")
        return None
    payload = {
        "contractName": "market",
        "contractAction": order_type,
        "contractPayload": {
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
        },
    }
    print(f"[ORDER] Broadcasting {order_type.upper()} {quantity} {symbol} @ {price} for {account_name}")
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
        print(f"[ORDER] Broadcast result type: {type(broadcast_result).__name__}")
        tx_id = None
        had_error = False
        if isinstance(broadcast_result, dict):
            if broadcast_result.get("error"):
                had_error = True
                print(f"[ORDER] Broadcast error payload: {broadcast_result.get('error')}")
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
        if tx_id:
            print(f"[ORDER] Broadcast success tx_id={tx_id}")
            return tx_id

        # Some nodes/clients broadcast successfully but do not return tx id.
        if not had_error:
            if isinstance(broadcast_result, dict):
                print(f"[ORDER] Broadcast succeeded without tx id. Keys: {list(broadcast_result.keys())}")
                result_obj = broadcast_result.get("result")
                if isinstance(result_obj, dict):
                    print(f"[ORDER] Broadcast result keys: {list(result_obj.keys())}")
            else:
                print(f"[ORDER] Broadcast succeeded without tx id. Raw type: {type(broadcast_result).__name__}")
            return "broadcast-ok-no-txid"

        print(f"[ORDER] Broadcast failed: no tx id returned for {symbol} {order_type}")
        return None
    except Exception as exc:
        print(f"[ORDER] Broadcast exception for {symbol} {order_type}: {exc}")
        tb = traceback.format_exc().strip()
        if tb:
            print(tb)
        return None

def place_order(account_name, token, price, quantity, order_type="buy", posting_key=None, active_key=None, nodes=None):
    _enforce_tx_delay()
    """Generic, safe order placement for any account/keys/nodes."""
    # Use env vars as fallback if not provided
    posting_key = posting_key or os.environ.get("HIVE_POSTING_KEY")
    active_key = active_key or os.environ.get("HIVE_ACTIVE_KEY")
    nodes = nodes or ["https://api.hive.blog", "https://anyx.io"]
    print(f"[ORDER] Request: account={account_name} type={order_type} token={token} qty={quantity} price={price}")
    if account_name in {"strangedad", "peakecoin.bnb"} and token.upper() == "SWAP.BCH" and order_type == "buy":
        print(f"[ORDER] Blocked SWAP.BCH buy for {account_name}.")
        return False
    if not active_key:
        print("[ORDER] Missing active key. Order cannot be signed.")
        return False
    # ...existing code...
    # Use SWAP.HIVE as the base token for all buy orders
    token_used = "SWAP.HIVE" if order_type == "buy" else token
    available = get_balance(account_name, token_used)
    print(f"[ORDER] Available balance for {token_used}: {available}")
    # ...existing code...
    if available < quantity:
        print(f"[ORDER] Adjusting quantity from {quantity} due to low balance")
        quantity = max(available * 0.95, 0.00001)
        print(f"[ORDER] Adjusted quantity: {quantity}")
    if quantity <= 0:
        print("[ORDER] Quantity is <= 0 after adjustment. Skipping order.")
        return False
    try:
        tx_id = build_and_send_op(account_name, token, price, quantity, order_type, posting_key, active_key, nodes)
        if tx_id:
            print(f"[ORDER] SUCCESS: tx_id={tx_id}")
            return True
        print(f"[ORDER] FAILED: no tx_id returned for {order_type} {token}")
        return False
    except Exception as exc:
        print(f"[ORDER] Exception while placing {order_type} for {token}: {exc}")
        tb = traceback.format_exc().strip()
        if tb:
            print(tb)
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
