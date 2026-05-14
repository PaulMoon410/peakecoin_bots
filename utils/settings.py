import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_list(name, default):
    value = os.getenv(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


SERVER_PORT = _get_int("PORT", _get_int("SERVER_PORT", 8080))
DEBUG_MODE = _get_bool("DEBUG_MODE", False)

DEFAULT_PROFIT_TARGET = _get_float("DEFAULT_PROFIT_TARGET", 2.0)
MIN_PROFIT_TARGET = _get_float("MIN_PROFIT_TARGET", 0.5)
MAX_PROFIT_TARGET = _get_float("MAX_PROFIT_TARGET", 20.0)

HIVE_NODES = _get_list(
    "HIVE_NODES",
    [
        "https://api.hive.blog",
        "https://anyx.io",
        "https://api.deathwing.me",
        "https://hived.emre.sh",
    ],
)
DEFAULT_HIVE_RC_NODE = os.getenv("DEFAULT_HIVE_RC_NODE", HIVE_NODES[0])
DEFAULT_ENGINE_NODE = os.getenv("DEFAULT_ENGINE_NODE", "https://api.hive-engine.com/rpc/contracts")

DEFAULT_DELAY = _get_int("DEFAULT_DELAY", 1500)
MIN_RESOURCE_CREDITS = _get_float("MIN_RESOURCE_CREDITS", 10.0)

SUPPORTED_CURRENCIES = _get_list(
    "SUPPORTED_CURRENCIES",
    ["BTC", "ETH", "DOGE", "LTC", "TETHER", "HBD", "BLURT"],
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = _get_bool("LOG_TO_FILE", True)
LOG_FILE = os.getenv("LOG_FILE", "peakebot.log")

REQUIRE_HTTPS = _get_bool("REQUIRE_HTTPS", False)
API_KEY_REQUIRED = _get_bool("API_KEY_REQUIRED", False)
WEB_API_KEY = os.getenv("WEB_API_KEY", "")

PEAKECOIN_USERNAME = os.getenv("PEAKECOIN_USERNAME", "").strip()
PEAKECOIN_CURRENCIES = _get_list("PEAKECOIN_CURRENCIES", [])


def get_active_key(currency):
    normalized = (currency or "").strip().upper().replace("-", "_")
    return os.getenv(f"PEAKECOIN_ACTIVE_KEY_{normalized}", "").strip()