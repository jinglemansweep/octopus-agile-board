import board
import gc
import microcontroller
import os
import time
import adafruit_datetime as datetime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_bitmap_font import bitmap_font
from adafruit_debouncer import Debouncer
from adafruit_display_text.label import Label
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from digitalio import DigitalInOut, Pull
from displayio import Group

from constants import (
    DEBUG,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
    MATRIX_BIT_DEPTH,
    MATRIX_COLOR_ORDER,
    NTP_UPDATE_HOURS,
    OCTOPUS_UPDATE_MINS,
    OCTOPUS_FETCH_PERIODS,
    TIME_ON,
    TIME_DARK,
    TIME_OFF,
    MODE_ON,
    MODE_DARK,
    MODE_OFF,
    MODES,
    Colors,
)

from utils import (
    logger,
    get_new_epochs,
    set_current_time,
    get_current_and_next_agile_rates,
    build_date_fmt,
    build_time_fmt,
    build_dow_fmt,
    rate_to_color,
)

from secrets import secrets

gc.collect()

logger(
    f"Config: debug={DEBUG} matrix_width={MATRIX_WIDTH} matrix_height={MATRIX_HEIGHT}"
)

# RGB MATRIX
logger("Configuring RGB Matrix")

gc.collect()
matrix = Matrix(
    width=MATRIX_WIDTH,
    height=MATRIX_HEIGHT,
    bit_depth=MATRIX_BIT_DEPTH,
    color_order=MATRIX_COLOR_ORDER,
)
display = matrix.display
gc.collect()

# STATIC RESOURCES
FONT = bitmap_font.load_font("assets/bitocra7.bdf")
gc.collect()

# SCREEN
root_group = Group()
blank_group = Group()
display.show(blank_group)

# NETWORKING
logger("Configuring Networking")
network = Network(status_neopixel=None, debug=DEBUG)
network.connect()
gc.collect()
mac = network._wifi.esp.MAC_address
host_id = "{:02x}{:02x}{:02x}{:02x}".format(mac[0], mac[1], mac[2], mac[3])
requests = network.requests
logger(f"Host ID: {host_id}")

# TIME
# set_current_time(requests)
# gc.collect()


# GPIO
pin_down = DigitalInOut(board.BUTTON_DOWN)
pin_down.switch_to_input(pull=Pull.UP)
button_down = Debouncer(pin_down)
pin_up = DigitalInOut(board.BUTTON_UP)
pin_up.switch_to_input(pull=Pull.UP)
button_up = Debouncer(pin_up)
gc.collect()

# STATE
frame = 0
state = {}

# THEME
COLOR_DIM = Colors.BLUE_DARK

# SPRITE: BORDER
border_pos = (0, 0)
border_size = (MATRIX_WIDTH, MATRIX_HEIGHT)
border_stroke = 1
border_rect = RoundRect(
    border_pos[0],
    border_pos[1],
    border_size[0],
    border_size[1],
    r=1,
    outline=COLOR_DIM,
    stroke=border_stroke,
)
root_group.append(border_rect)

# SPRITE: DAY
dow_pos = (2, 4)
dow_pos_dark = (0, 2)
dow_label = Label(
    x=dow_pos[0],
    y=dow_pos[1],
    font=FONT,
    text="...",
    color=Colors.MAGENTA_DARK,
)
root_group.append(dow_label)

# SPRITE: DATE
date_pos = (16, 4)
date_pos_dark = (15, 2)
date_label = Label(
    x=date_pos[0],
    y=date_pos[1],
    font=FONT,
    text="../..",
    color=Colors.MAGENTA_DARK,
)
root_group.append(date_label)

# SPRITE: TIME
time_pos = (43, 4)
time_pos_dark = (45, 2)
time_label = Label(
    x=time_pos[0],
    y=time_pos[1],
    font=FONT,
    text="..:..",
    color=Colors.WHITE_DARK,
)
root_group.append(time_label)

# SPRITE: RATE 0 (NOW)
rate0_pos = (4, 11)
rate0_pos_dark = (0, 29)
rate0_size = (20, 16)
rate0_label_offset = (3, 7)
rate0_rect = RoundRect(
    rate0_pos[0],
    rate0_pos[1],
    rate0_size[0],
    rate0_size[1],
    r=1,
    outline=COLOR_DIM,
)
root_group.append(rate0_rect)
rate0_label = Label(
    x=rate0_pos[0] + rate0_label_offset[0],
    y=rate0_pos[1] + rate0_label_offset[1],
    font=FONT,
    text="00",
    color=COLOR_DIM,
    scale=2,
)
root_group.append(rate0_label)

# SPRITE: RATE 1 (NEXT)
rate1_pos = (27, 11)
rate1_pos_dark = (12, 29)
rate1_size = (15, 11)
rate1_label_offset = (4, 5)
rate1_rect = RoundRect(
    rate1_pos[0],
    rate1_pos[1],
    rate1_size[0],
    rate1_size[1],
    r=1,
    outline=COLOR_DIM,
)
root_group.append(rate1_rect)
rate1_label = Label(
    x=rate1_pos[0] + rate1_label_offset[0],
    y=rate1_pos[1] + rate1_label_offset[1],
    font=FONT,
    text="00",
    color=COLOR_DIM,
)
root_group.append(rate1_label)

# SPRITE: RATE 2 (LATER)
rate2_pos = (45, 11)
rate2_pos_dark = (12, 29)
rate2_size = (15, 11)
rate2_label_offset = (4, 5)
rate2_rect = RoundRect(
    rate2_pos[0],
    rate2_pos[1],
    rate2_size[0],
    rate2_size[1],
    r=1,
    outline=COLOR_DIM,
)
root_group.append(rate2_rect)
rate2_label = Label(
    x=rate2_pos[0] + rate2_label_offset[0],
    y=rate2_pos[1] + rate2_label_offset[1],
    font=FONT,
    text="00",
    color=COLOR_DIM,
)
root_group.append(rate2_label)

# SPRITE: DEBUG (FREE MEMORY)
debug_pos = (35, 27)
debug_pos_dark = (0, 8)
debug_label = Label(
    x=debug_pos[0],
    y=debug_pos[1],
    font=FONT,
    text="",
    color=COLOR_DIM,
)
if DEBUG:
    root_group.append(debug_label)

gc.collect()
display.show(root_group)
gc.collect()

# DRAW
def draw(frame, now, state):

    dow_label.text = build_dow_fmt(now)
    dow_label.x = dow_pos[0] if state["mode"] == MODE_ON else dow_pos_dark[0]
    dow_label.y = dow_pos[1] if state["mode"] == MODE_ON else dow_pos_dark[1]

    date_label.text = build_date_fmt(now)
    date_label.x = date_pos[0] if state["mode"] == MODE_ON else date_pos_dark[0]
    date_label.y = date_pos[1] if state["mode"] == MODE_ON else date_pos_dark[1]

    time_label.text = build_time_fmt(now)
    time_label.x = time_pos[0] if state["mode"] == MODE_ON else time_pos_dark[0]
    time_label.y = time_pos[1] if state["mode"] == MODE_ON else time_pos_dark[1]

    debug_label.text = f"{state['mode']} {gc.mem_free()} "
    debug_label.x = debug_pos[0] if state["mode"] == MODE_ON else debug_pos_dark[0]
    debug_label.y = debug_pos[1] if state["mode"] == MODE_ON else debug_pos_dark[1]

    if "rates" in state:

        rate0_value, rate1_value, rate2_value = (
            state["rates"][0][1],
            state["rates"][1][1],
            state["rates"][2][1],
        )

        # BORDER

        border_rect.outline = rate_to_color(
            rate0_value, Colors.GREEN_DARK, Colors.RED_DARK, Colors.OFF
        )

        # RATE 0

        rate0_rect.outline = rate_to_color(
            rate0_value, Colors.GREEN_DARK, Colors.RED_DARK, COLOR_DIM
        )
        rate0_label.text = f"{int(round(rate0_value))}"
        rate0_label.color = rate_to_color(
            rate0_value, Colors.GREEN_DARK, Colors.RED_DARK, COLOR_DIM
        )
        rate0_label.x = rate0_pos[0] + rate0_label_offset[0]
        rate0_label.y = rate0_pos[1] + rate0_label_offset[1]

        # RATE 1

        rate1_rect.outline = rate_to_color(
            rate1_value, Colors.GREEN_DARK, Colors.RED_DARK, COLOR_DIM
        )

        rate1_label.text = f"{int(round(rate1_value))}"
        rate1_label.color = rate_to_color(
            rate0_value, Colors.WHITE_DARK, Colors.WHITE_DARK, COLOR_DIM
        )
        rate1_label.x = rate1_pos[0] + rate1_label_offset[0]
        rate1_label.y = rate1_pos[1] + rate1_label_offset[1]

        # RATE 1

        rate2_rect.outline = rate_to_color(
            rate2_value, Colors.GREEN_DARK, Colors.RED_DARK, COLOR_DIM
        )

        rate2_label.text = f"{int(round(rate2_value))}"
        rate2_label.color = rate_to_color(
            rate2_value, Colors.WHITE_DARK, Colors.WHITE_DARK, COLOR_DIM
        )
        rate2_label.x = rate2_pos[0] + rate2_label_offset[0]
        rate2_label.y = rate2_pos[1] + rate2_label_offset[1]


# APP LOGIC

logger("Start Event Loop")
ready = False
ready_time = False
ready_agile = False
ts = time.monotonic()

mode_idx = 0
error_count = 0

try:
    while True:

        # LOOP STATE
        now = datetime.datetime.now().timetuple()
        ts, (new_hour, new_min, new_sec) = get_new_epochs(ts)
        state["mode"] = MODES[mode_idx]
        ready = all([ready_time, ready_agile])

        # MODE BUTTONS

        button_down.update()
        button_up.update()
        if button_down.fell or button_up.fell:
            mode_idx += 1
            if mode_idx > len(MODES) - 1:
                mode_idx = 0
            logger(f"Button: Mode Switch: {mode_idx}")

        # DEBUG

        if frame % 10 == 0:
            logger(f"Debug: Ready={ready} Frame={frame} State={state}")

        # DRAW DISPLAY

        if new_sec and ready:
            try:
                display.brightness = 1.0 if state["mode"] != MODE_OFF else 0.0
                draw(frame, now, state)
            except Exception as e:
                logger(f"Error: Draw Exception: {e}")

        # PERIODIC UPDATE: NTP

        if (new_hour and now.tm_hour % NTP_UPDATE_HOURS == 0) or not ready_time:
            logger(f"NTP: Fetch Time")
            try:
                set_current_time(requests)
                gc.collect()
                ready_time = True
            except Exception as e:
                logger(f("NTP: Fetch Error: {e}"))
                error_count += 1

        # PERIODIC UPDATE: AGILE RATES

        if ready_time and (
            (new_min and now.tm_min % OCTOPUS_UPDATE_MINS == 0) or not ready_agile
        ):
            try:
                state["rates"] = get_current_and_next_agile_rates(
                    requests, OCTOPUS_FETCH_PERIODS
                )
                gc.collect()
                logger(f"Fetch: Rates={state['rates']}")
                ready_agile = True
            except Exception as e:
                logger(f"Error: Octopus Fetch Exception: {e}")
                error_count += 1

        # HANDLE PERSISTENT ERRORS

        if error_count > 10:
            raise Exception("Too Many Errors")

        frame += 1
        time.sleep(0.1)
        gc.collect()


except Exception as e:
    logger(f"Error: Fatal Exception: {e}")
    time.sleep(10 if DEBUG else 1)
    microcontroller.reset()
