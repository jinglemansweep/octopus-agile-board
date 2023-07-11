import board
import gc
import os
import terminalio
import time
import adafruit_datetime as datetime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_lis3dh import LIS3DH_I2C
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from busio import I2C
from displayio import Group

from app.constants import (
    DEBUG,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
    MATRIX_BIT_DEPTH,
    MATRIX_COLOR_ORDER,
    COLORS_RAINBOW,
    COLOR_RED_DARK,
    COLOR_BLUE_DARK,
    COLOR_GREEN_DARK,
)

from app.graphics import make_box, rate_to_color

from app.utils import (
    logger,
    matrix_rotation,
    get_new_epochs,
    set_current_time,
    get_current_and_next_agile_rates,
    color_brightness,
    build_splash_group,
)

# STATIC RESOURCES
FONT_NORMAL = terminalio.FONT
FONT_SMALL = bitmap_font.load_font("assets/bitocra7.bdf")

gc.collect()


# Local Classes
class CellLabel(Label):
    def __init__(self, text, color=0x222222, font=FONT_NORMAL, x=0, y=0):
        super().__init__(x=x, y=y, text=text, color=color, font=font)


logger(
    f"Config: debug={DEBUG} matrix_width={MATRIX_WIDTH} matrix_height={MATRIX_HEIGHT}"
)

# RGB MATRIX
logger("Configuring RGB Matrix")
matrix = Matrix(
    width=MATRIX_WIDTH,
    height=MATRIX_HEIGHT,
    bit_depth=MATRIX_BIT_DEPTH,
    color_order=MATRIX_COLOR_ORDER,
)
accelerometer = LIS3DH_I2C(I2C(board.SCL, board.SDA), address=0x19)
_ = accelerometer.acceleration  # drain startup readings

# SPLASH
splash_group = build_splash_group(FONT_SMALL, "jinglemansweep", COLORS_RAINBOW)

# DISPLAY / FRAMEBUFFER
logger("Configuring Display")
display = matrix.display
display.rotation = matrix_rotation(accelerometer)
display.show(splash_group)
del accelerometer

# NETWORKING
logger("Configuring Networking")
network = Network(status_neopixel=None, debug=DEBUG)
network.connect()
mac = network._wifi.esp.MAC_address
host_id = "{:02x}{:02x}{:02x}{:02x}".format(mac[0], mac[1], mac[2], mac[3])
requests.set_socket(socket, network._wifi.esp)
logger(f"Host ID: {host_id}")


# TIME
set_current_time()

# API TEST
# rates = get_current_and_next_agile_rates()
# logger(f"Rates: {rates}")

# SCREEN
root_group = Group()

# Date
box_date = make_box(1, 1, 42, 7, font=FONT_SMALL, background_color=COLOR_RED_DARK)
root_group.append(box_date)

# Time
box_time = make_box(41, 1, 22, 7, font=FONT_SMALL, background_color=COLOR_BLUE_DARK)
root_group.append(box_time)

rate_offset_y = 11

# Electricity Rates
box_rate_elec_now = make_box(
    10, rate_offset_y, 24, 11, font=FONT_NORMAL, background_color=COLOR_GREEN_DARK, text_offset=4
)
root_group.append(box_rate_elec_now)
box_rate_elec_next = make_box(
    40, rate_offset_y+4, 24, 7, font=FONT_SMALL, background_color=COLOR_GREEN_DARK
)
root_group.append(box_rate_elec_next)

# Electricity Status
rect_rate_elec_status = Rect(1, 25, 62, 6, fill=COLOR_RED_DARK)
root_group.append(rect_rate_elec_status)

# DRAW
def draw(state):
    now_tuple = datetime.datetime.now().timetuple()
    now_day_name = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"][now_tuple.tm_wday]
    now_month_name = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ][now_tuple.tm_mon - 1]
    box_date[1].text = f"{now_day_name} {now_tuple.tm_mon:02} {now_month_name}"
    box_time[1].text = f"{now_tuple.tm_hour:02}:{now_tuple.tm_min:02}"
    if "rates" in state:
        rate_now, rate_next = state['rates'][0][1], state['rates'][1][1]
        box_rate_elec_now[1].text = f"{int(rate_now*100)}p"
        box_rate_elec_now[0].fill = rate_to_color(rate_now)
        box_rate_elec_next[1].text = f"{int(rate_next*100)}p"
        box_rate_elec_next[0].fill = rate_to_color(rate_next)
        rect_rate_elec_status.fill = rate_to_color(rate_now)
    if state["frame"] % 10 == 0:
        logger(f"Draw: state={state}")


# STATE
state = dict(frame=0)


# APP STARTUP
def run():
    global state
    gc.collect()
    logger("Start Event Loop")
    display.show(root_group)
    second = None
    first_run = True
    while True:
        gc.collect()
        now = datetime.datetime.now().timetuple()
        if second != now.tm_sec:
            second = now.tm_sec
            if second % 60 == 0 or first_run:
                first_run = False
                logger(f"Minute")
                state["rates"] = get_current_and_next_agile_rates()
        try:
            draw(state)
        except Exception as e:
            print("EXCEPTION", e)
        state["frame"] += 1
        time.sleep(0.1)


# STARTUP
run()
