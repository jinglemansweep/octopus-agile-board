from secrets import secrets

# CONFIG / SECRETS
DEBUG = secrets.get("debug", False)
BRIGHTNESS = secrets.get("brightness", 0.2)
NTP_TIMEZONE = secrets.get("timezone", "Europe/London")

OCTOPUS_API_URL = secrets.get("octopus_api_url", "https://api.octopus.energy")
OCTOPUS_PRODUCT_CODE = secrets.get("octopus_product_code", "AGILE-18-02-21")

TILE_ROWS = secrets.get("tile_rows", 2)
TILE_COLS = secrets.get("tile_cols", 2)
MATRIX_WIDTH = secrets.get("matrix_width", 64)
MATRIX_HEIGHT = secrets.get("matrix_height", 32)
MATRIX_BIT_DEPTH = secrets.get("matrix_bit_depth", 4)
MATRIX_COLOR_ORDER = secrets.get("matrix_color_order", "RGB")


