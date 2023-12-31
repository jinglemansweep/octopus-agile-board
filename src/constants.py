from secrets import secrets

# CONFIG / SECRETS
DEBUG = secrets.get("debug", False)
DEBUG_MODE_FORCE = secrets.get("debug_mode_force")

NTP_TIMEZONE = secrets.get("timezone", "Europe/London")

MATRIX_WIDTH = secrets.get("matrix_width", 64)
MATRIX_HEIGHT = secrets.get("matrix_height", 32)
MATRIX_BIT_DEPTH = secrets.get("matrix_bit_depth", 3)
MATRIX_COLOR_ORDER = secrets.get("matrix_color_order", "RGB")

NTP_UPDATE_HOURS = int(secrets.get("ntp_update_hours", 3))

TIME_ON = secrets.get("time_on", "09:00")
TIME_DARK = secrets.get("time_dark", "21:00")
TIME_OFF = secrets.get("time_off", "23:00")

OCTOPUS_API_URL = secrets.get("octopus_api_url", "https://api.octopus.energy")
OCTOPUS_PRODUCT_CODE = secrets.get("octopus_product_code", "AGILE-FLEX-22-11-25")
OCTOPUS_UPDATE_MINS = int(secrets.get("octopus_update_mins", 30))
OCTOPUS_FETCH_PERIODS = int(secrets.get("octopus_fetch_periods", 3))
OCTOPUS_RATE_LOW = int(secrets.get("octopus_rate_low", 10))
OCTOPUS_RATE_HIGH = int(secrets.get("octopus_rate_high", 30))

MQTT_BROKER = secrets.get("mqtt_broker", "homeassistant.local")
MQTT_PORT = secrets.get("mqtt_port", 1883)
MQTT_USERNAME = secrets.get("mqtt_username")
MQTT_PASSWORD = secrets.get("mqtt_password")
MQTT_TOPIC_PREFIX = secrets.get("mqtt_topic_prefix", "agileboard")

# CONSTANTS


class Colors:
    OFF = 0x000000
    WHITE = 0xFFFFFF
    WHITE_DARK = 0x333333
    RED = 0xFF0000
    RED_DARK = 0x330000
    GREEN = 0x00FF00
    GREEN_DARK = 0x003300
    BLUE = 0x0000FF
    BLUE_DARK = 0x000033
    MAGENTA = 0xFF00FF
    MAGENTA_DARK = 0x330033
    YELLOW = 0xFFFF00
    YELLOW_DARK = 0x333300
    CYAN = 0x00FFFF
    CYAN_DARK = 0x003333


WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MODE_OFF = 0
MODE_ON = 1
MODE_DARK = 2

MODES = [MODE_ON, MODE_OFF]  # Dark Mode Disabled For Now
