# Legacy configuration reference
# Runtime settings now load from .env via utils/settings.py.
# Copy .env.example to .env and set your values there instead.

# Server Settings
SERVER_PORT = 8080
DEBUG_MODE = False

# Bot Settings
DEFAULT_PROFIT_TARGET = 2.0  # Default profit percentage
MIN_PROFIT_TARGET = 0.5
MAX_PROFIT_TARGET = 20.0

# Hive Network Settings
HIVE_NODES = [
    "https://api.hive.blog",
    "https://anyx.io",
    "https://api.deathwing.me",
    "https://hived.emre.sh"
]

# Trading Settings
DEFAULT_DELAY = 1500  # 25 minutes in seconds
MIN_RESOURCE_CREDITS = 10.0  # Minimum RC percentage to trade

# Supported Currencies
SUPPORTED_CURRENCIES = [
    "BTC", "ETH", "DOGE", "LTC", "TETHER", "HBD", "BLURT"
]

# Logging Settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_FILE = "peakebot.log"

# Security Settings
REQUIRE_HTTPS = False  # Set to True for production
API_KEY_REQUIRED = False  # Set to True for production with API access
