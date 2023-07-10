from secrets import secrets

# CONFIG / SECRETS
DEBUG = secrets.get("debug", False)
NTP_TIMEZONE = secrets.get("timezone", "Europe/London")

OCTOPUS_API_URL = secrets.get("octopus_api_url", "https://api.octopus.energy")
OCTOPUS_PRODUCT_CODE = secrets.get("octopus_product_code", "AGILE-FLEX-22-11-25")

MATRIX_WIDTH = secrets.get("matrix_width", 64)
MATRIX_HEIGHT = secrets.get("matrix_height", 32)
MATRIX_BIT_DEPTH = secrets.get("matrix_bit_depth", 4)
MATRIX_COLOR_ORDER = secrets.get("matrix_color_order", "RGB")


