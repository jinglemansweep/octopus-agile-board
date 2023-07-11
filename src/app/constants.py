import os

# CONFIG / SECRETS
DEBUG = os.getenv("DEBUG", False)
NTP_TIMEZONE = os.getenv("TIMEZONE", "Europe/London")

OCTOPUS_API_URL = os.getenv("OCTOPUS_API_URL", "https://api.octopus.energy")
OCTOPUS_PRODUCT_CODE = os.getenv("OCTOPUS_PRODUCT_CODE", "AGILE-FLEX-22-11-25")

MATRIX_WIDTH = os.getenv("MATRIX_WIDTH", 64)
MATRIX_HEIGHT = os.getenv("MATRIX_HEIGHT", 32)
MATRIX_BIT_DEPTH = os.getenv("MATRIX_BIT_DEPTH", 3)
MATRIX_COLOR_ORDER = os.getenv("MATRIX_COLOR_ORDER", "RGB")

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