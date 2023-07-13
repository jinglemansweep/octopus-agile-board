
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
#set_current_time(requests)
#gc.collect()


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
COLOR_DIMMED = Colors.BLUE_DARK

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
    outline=COLOR_DIMMED,
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

# SPRITE: RATE NOW
ratenow_pos = (7, 11)
ratenow_pos_dark = (0, 29)
ratenow_size = (21, 11)
ratenow_rect = RoundRect(
    ratenow_pos[0],
    ratenow_pos[1],
    ratenow_size[0],
    ratenow_size[1],
    r=1,
    outline=COLOR_DIMMED,
)
root_group.append(ratenow_rect)
ratenow_label = Label(
    x=ratenow_pos[0] + 3,
    y=ratenow_pos[1] + 5,
    font=FONT,
    text=".",
    color=Colors.YELLOW_DARK,
)
root_group.append(ratenow_label)

# SPRITE: RATE NEXT
ratenext_pos = (35, 11)
ratenext_pos_dark = (12, 29)
ratenext_size = (21, 11)
ratenext_rect = RoundRect(
    ratenext_pos[0],
    ratenext_pos[1],
    ratenext_size[0],
    ratenext_size[1],
    r=1,
    outline=COLOR_DIMMED,
)
root_group.append(ratenext_rect)
ratenext_label = Label(
    x=ratenext_pos[0] + 3,
    y=ratenext_pos[1] + 5,
    font=FONT,
    text=".",
    color=Colors.YELLOW_DARK,
)
root_group.append(ratenext_label)

# SPRITE: DEBUG (FREE MEMORY)
debug_pos = (35, 27)
debug_pos_dark = (0, 8)
debug_label = Label(
    x=debug_pos[0],
    y=debug_pos[1],
    font=FONT,
    text="",
    color=COLOR_DIMMED,
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

        # need to convert current time to 30 min period, plus the next period, and use as lookup in "rates" object
        # e.g. [("2023-07-14-T22:00:00", 0.245), ("2023-07-14-T22:30:00", 0.245)]

        ratenow_value, ratenext_value = state["rates"][0][1], state["rates"][1][1]

        border_rect.outline = (
            rate_to_color(ratenow_value, Colors.GREEN_DARK, Colors.RED_DARK, Colors.OFF)
            if state["mode"] == MODE_ON
            else Colors.OFF
        )

        ratenow_rect.outline = (
            rate_to_color(ratenow_value, Colors.GREEN_DARK, Colors.RED_DARK, Colors.BLUE_DARK)
            if state["mode"] == MODE_ON
            else Colors.OFF
        )
        ratenow_label.text = f"{int(round(ratenow_value))}"
        ratenow_label.color = (
            rate_to_color(
                ratenow_value, Colors.WHITE_DARK, Colors.WHITE_DARK, Colors.YELLOW_DARK
            )
            if state["mode"] == MODE_ON
            else rate_to_color(
                ratenow_value, Colors.GREEN_DARK, Colors.RED_DARK, Colors.MAGENTA_DARK
            )
        )
        ratenow_label.x = (
            ratenow_pos[0] + 3 if state["mode"] == MODE_ON else ratenow_pos_dark[0]
        )
        ratenow_label.y = (
            ratenow_pos[1] + 5 if state["mode"] == MODE_ON else ratenow_pos_dark[1]
        )

        ratenext_rect.outline = (
            rate_to_color(ratenext_value, Colors.GREEN_DARK, Colors.RED_DARK, Colors.BLUE_DARK)
            if state["mode"] == MODE_ON
            else Colors.OFF
        )
        ratenext_label.text = f"{int(round(ratenext_value))}"
        ratenext_label.color = rate_to_color(
            ratenow_value, Colors.WHITE_DARK, Colors.WHITE_DARK, Colors.YELLOW_DARK
        ) if state["mode"] == MODE_ON else rate_to_color(
                ratenext_value, Colors.GREEN_DARK, Colors.RED_DARK, Colors.MAGENTA_DARK
        )
        ratenext_label.x = (
            ratenext_pos[0] + 3 if state["mode"] == MODE_ON else ratenext_pos_dark[0]
        )
        ratenext_label.y = (
            ratenext_pos[1] + 5 if state["mode"] == MODE_ON else ratenext_pos_dark[1]
        )

# APP LOGIC

logger("Start Event Loop")
initialised = False
ts = time.monotonic()

mode_idx = 0
error_count = 0

try:
    while True:
        now = datetime.datetime.now().timetuple()
        ts, (new_hour, new_min, new_sec) = get_new_epochs(ts)

        state["mode"] = MODES[mode_idx]

        # MODE BUTTONS

        button_down.update()
        button_up.update()
        if button_down.fell or button_up.fell:
            mode_idx += 1
            if mode_idx > len(MODES) - 1:
                mode_idx = 0
            logger(f"Button: Mode Switch: {mode_idx}")
        
        # DRAW DISPLAY

        if new_sec or not initialised:
            if frame % 10 == 0:
                logger(f"Debug: Frame={frame} State={state}")
            try:
                display.brightness = 1.0 if state["mode"] != MODE_OFF else 0.0
                draw(frame, now, state)
            except Exception as e:
                logger(f"Error: Draw Exception: {e}")

        # PERIODIC UPDATE: AGILE RATES

        if (new_min and now.tm_min % OCTOPUS_UPDATE_MINS == 0) or not initialised:
            try:
                state["rates"] = get_current_and_next_agile_rates(
                    requests, OCTOPUS_FETCH_PERIODS
                )
                gc.collect()
                logger(f"Fetch: Rates={state['rates']}")
                initialised = True
            except Exception as e:
                logger(f"Error: Octopus Fetch Exception: {e}")
                error_count += 1

        # PERIODIC UPDATE: NTP

        if (new_hour and now.tm_hour % NTP_UPDATE_HOURS == 0) or not initialised:
            logger(f"NTP: Fetch Time")
            try:
                set_current_time(requests)
                gc.collect()
            except Exception as e:
                logger(f("NTP: Fetch Error: {e}"))
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
