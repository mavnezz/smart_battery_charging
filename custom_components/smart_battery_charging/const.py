"""Constants for Smart Battery Charging integration."""

DOMAIN = "smart_battery_charging"
VERSION = "0.2.7"

# Configuration keys
CONF_TIBBER_TOKEN = "tibber_token"
CONF_HOME_ID = "home_id"
CONF_PRICE_RESOLUTION = "price_resolution"
CONF_CHARGE_WINDOWS = "charge_windows"
CONF_DISCHARGE_WINDOWS = "discharge_windows"
CONF_CHEAP_PERCENTILE = "cheap_percentile"
CONF_EXPENSIVE_PERCENTILE = "expensive_percentile"
CONF_MIN_SPREAD = "min_spread"
CONF_BATTERY_CAPACITY = "battery_capacity"
CONF_BATTERY_EFFICIENCY = "battery_efficiency"

# Zendure configuration
CONF_ZENDURE_ACCOUNT = "zendure_account"
CONF_ZENDURE_PASSWORD = "zendure_password"
CONF_ZENDURE_DEVICE_ID = "zendure_device_id"

# Tibber API
TIBBER_API_ENDPOINT = "https://api.tibber.com/v1-beta/gql"

# Price resolution options
RESOLUTION_HOURLY = "HOURLY"
RESOLUTION_QUARTERLY = "QUARTER_HOURLY"

# Default values
DEFAULT_CHARGE_WINDOWS = 6
DEFAULT_DISCHARGE_WINDOWS = 3
DEFAULT_CHEAP_PERCENTILE = 25
DEFAULT_EXPENSIVE_PERCENTILE = 75
DEFAULT_MIN_SPREAD = 20  # Minimum price spread in %
DEFAULT_BATTERY_EFFICIENCY = 0.85  # 85% round-trip efficiency

# Operational states
STATE_CHARGE = "charge"
STATE_DISCHARGE = "discharge"
STATE_IDLE = "idle"
STATE_OFF = "off"

# Price levels from Tibber
PRICE_LEVEL_VERY_CHEAP = "VERY_CHEAP"
PRICE_LEVEL_CHEAP = "CHEAP"
PRICE_LEVEL_NORMAL = "NORMAL"
PRICE_LEVEL_EXPENSIVE = "EXPENSIVE"
PRICE_LEVEL_VERY_EXPENSIVE = "VERY_EXPENSIVE"

# Sensor attributes
ATTR_PRICES_TODAY = "prices_today"
ATTR_PRICES_TOMORROW = "prices_tomorrow"
ATTR_TOMORROW_VALID = "tomorrow_valid"
ATTR_CHEAPEST_WINDOWS = "cheapest_windows"
ATTR_EXPENSIVE_WINDOWS = "expensive_windows"
ATTR_CURRENT_PRICE = "current_price"
ATTR_CURRENT_LEVEL = "current_level"
ATTR_RECOMMENDED_STATE = "recommended_state"
ATTR_NEXT_CHEAP_WINDOW = "next_cheap_window"
ATTR_NEXT_EXPENSIVE_WINDOW = "next_expensive_window"
ATTR_AVERAGE_PRICE_TODAY = "average_price_today"
ATTR_POTENTIAL_SAVINGS = "potential_savings"

# Update intervals
UPDATE_INTERVAL_MINUTES = 5
PRICE_FETCH_INTERVAL_HOURS = 1

# Platforms
PLATFORMS = ["sensor", "number", "select"]
