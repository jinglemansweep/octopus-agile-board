from secrets import secrets

# CONFIG / SECRETS
DEBUG = secrets.get("debug", False)
NTP_TIMEZONE = secrets.get("timezone", "Europe/London")

MATRIX_WIDTH = secrets.get("matrix_width", 64)
MATRIX_HEIGHT = secrets.get("matrix_height", 32)
MATRIX_BIT_DEPTH = secrets.get("matrix_bit_depth", 3)
MATRIX_COLOR_ORDER = secrets.get("matrix_color_order", "RGB")

NTP_UPDATE_HOURS = int(secrets.get("ntp_update_hours", 3))

TIMER_FORCE = secrets.get("timer_force")
TIMER_WAKE = secrets.get("timer_wake", 9)
TIMER_DARK = secrets.get("timer_dark", 18)
TIMER_SLEEP = secrets.get("timer_sleep", 22)

OCTOPUS_API_URL = secrets.get("octopus_api_url", "https://api.octopus.energy")
OCTOPUS_PRODUCT_CODE = secrets.get("octopus_product_code", "AGILE-FLEX-22-11-25")
OCTOPUS_UPDATE_MINS = int(secrets.get("octopus_update_mins", 5))
OCTOPUS_RATE_LOW = int(secrets.get("octopus_rate_low", 10))
OCTOPUS_RATE_HIGH = int(secrets.get("octopus_rate_high", 30))

MQTT_BROKER = secrets.get("mqtt_broker", "homeassistant.local")
MQTT_PORT = secrets.get("mqtt_port", 1883)
MQTT_USERNAME = secrets.get("mqtt_username")
MQTT_PASSWORD = secrets.get("mqtt_password")
MQTT_TOPIC_PREFIX = secrets.get("mqtt_topic_prefix", "agileboard")

# CONSTANTS
COLOR_WHITE = 0xFFFFFF
COLOR_WHITE_DARK = 0x333333
COLOR_RED = 0xFF0000
COLOR_RED_DARK = 0x330000
COLOR_GREEN = 0x00FF00
COLOR_GREEN_DARK = 0x003300
COLOR_BLUE = 0x0000FF
COLOR_BLUE_DARK = 0x000033
COLOR_MAGENTA = 0xFF00FF
COLOR_MAGENTA_DARK = 0x330033
COLOR_YELLOW = 0xFFFF00
COLOR_YELLOW_DARK = 0x333300
COLOR_CYAN = 0x00FFFF
COLOR_CYAN_DARK = 0x003333

COLORS_RAINBOW = [
    COLOR_RED_DARK,
    COLOR_RED,
    COLOR_YELLOW_DARK,
    COLOR_YELLOW,
    COLOR_GREEN,
    COLOR_GREEN_DARK,
    COLOR_BLUE_DARK,
    COLOR_BLUE,
    COLOR_CYAN_DARK,
    COLOR_CYAN,
    COLOR_MAGENTA_DARK,
    COLOR_MAGENTA,
]

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
