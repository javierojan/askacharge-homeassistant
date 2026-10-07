"""Constants for the askacharge.com integration."""
from datetime import timedelta

DOMAIN = "askacharge"
DEFAULT_BASE_URL = "https://askacharge.com/askacharge/api"
CONF_BASE_URL = "base_url"
SCAN_INTERVAL = timedelta(seconds=30)

# OCPP 1.6 / 2.0.1 connector states as askacharge.com reports them (lower case for HA enum sensors)
STATUSES = [
    "available", "preparing", "charging", "suspendedev", "suspendedevse", "finishing",
    "reserved", "unavailable", "faulted", "occupied", "offline", "unknown",
]
