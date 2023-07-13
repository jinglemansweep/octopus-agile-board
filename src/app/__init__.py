import board
import gc
import microcontroller
import os
import time
import adafruit_datetime as datetime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from displayio import Group

from app.constants import (
    DEBUG,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
    MATRIX_BIT_DEPTH,
    MATRIX_COLOR_ORDER,
    NTP_UPDATE_HOURS,
    OCTOPUS_UPDATE_HOURS,
    OCTOPUS_FETCH_PERIODS,
    TIMER_FORCE,
    MQTT_TOPIC_PREFIX,
    Colors
)

from app.utils import (
    logger,
    matrix_rotation,
    get_new_epochs,
    set_current_time,
    get_current_and_next_agile_rates,
    find_lowest_contiguous_period,
    build_date_fmt,
    build_time_fmt,
    build_dow_fmt,
    get_timer_mode,
    rate_to_color,
)

from secrets import secrets

logger(
    f"Config: debug={DEBUG} matrix_width={MATRIX_WIDTH} matrix_height={MATRIX_HEIGHT}"
)

gc.collect()

# RGB MATRIX
logger("Configuring RGB Matrix")


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

# SPLASH - KEEP SIMPLE, USES RAM
splash_group = Group()  # build_splash_group(FONT, "jinglemansweep", COLORS_RAINBOW)
display.show(splash_group)

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
set_current_time(requests)
gc.collect()

# SCREEN
root_group = Group()
blank_group = Group()

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

# SPRITE: CHEAPEST RATE
cheaprate_pos = (2, 27)
cheaprate_label = Label(
    x=cheaprate_pos[0],
    y=cheaprate_pos[1],
    font=FONT,
    text="",
    color=COLOR_DIMMED,
)
root_group.append(cheaprate_label)

# SPRITE: DEBUG (FREE MEMORY)
debug_pos = (32, 27)
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
# del splash_group
gc.collect()

# DRAW
def draw(frame, now, state):

    dow_label.text = build_dow_fmt(now)
    date_label.text = build_date_fmt(now)

    time_label.text = build_time_fmt(now)
    time_label.x = time_pos[0] if state["mode"] == "on" else 45
    time_label.y = time_pos[1] if state["mode"] == "on" else 2

    debug_label.text = f"{gc.mem_free()} {state['mode']}"

    if "rates" in state:

        # need to convert current time to 30 min period, plus the next period, and use as lookup in "rates" object
        # e.g. [("2023-07-14-T22:00:00", 0.245), ("2023-07-14-T22:30:00", 0.245)]

        ratenow_value, ratenext_value = state["rates"][0][1], state["rates"][1][1]

        border_rect.outline = (
            rate_to_color(ratenow_value, Colors.GREEN_DARK, Colors.RED_DARK, None)
            if state["mode"] == "on"
            else None
        )

        ratenow_rect.outline = (
            rate_to_color(ratenow_value, Colors.GREEN_DARK, Colors.RED_DARK, None)
            if state["mode"] == "on"
            else None
        )
        ratenow_label.text = f"{int(round(ratenow_value))}"
        ratenow_label.color = rate_to_color(
            ratenow_value, Colors.WHITE_DARK, Colors.WHITE_DARK, Colors.YELLOW_DARK
        )
        ratenow_label.x = ratenow_pos[0] + 3 if state["mode"] == "on" else 0
        ratenow_label.y = ratenow_pos[1] + 5 if state["mode"] == "on" else 29

        ratenext_rect.outline = (
            rate_to_color(ratenext_value, Colors.GREEN_DARK, Colors.RED_DARK, None)
            if state["mode"] == "on"
            else None
        )
        ratenext_label.text = f"{int(round(ratenext_value))}"
        ratenext_label.color = (
            rate_to_color(
                ratenow_value, Colors.WHITE_DARK, Colors.WHITE_DARK, Colors.YELLOW_DARK
            )
            if state["mode"] == "on"
            else None
        )

        cheaprate_label.text = f"{state['period_lowest']}"
        cheaprate_label.color = (
            Colors.BLUE_DARK if state["mode"] == "on" else None
        )


# STATE
frame = 0
state = {}


# APP LOGIC

logger("Start Event Loop")
initialised = False
ts = time.monotonic()

try:
    while True:
        now = datetime.datetime.now().timetuple()
        ts, (new_hour, new_min, new_sec) = get_new_epochs(ts)

        if (new_hour and now.tm_hour % NTP_UPDATE_HOURS == 0) or not initialised:
            logger(f"NTP: Fetch Time")
            set_current_time(requests)
            gc.collect()

        if (new_hour and now.tm_hour % OCTOPUS_UPDATE_HOURS == 0) or not initialised:
            try:
                state["rates"] = get_current_and_next_agile_rates(
                    requests, OCTOPUS_FETCH_PERIODS
                )
                state["period_lowest"] = find_lowest_contiguous_period(
                    state["rates"], 4
                )[-8:-3]
                gc.collect()
                logger(f"Fetch: Rates={state['rates']}")
                initialised = True
            except Exception as e:
                logger(f"Error: Octopus Fetch Exception: {e}")

        if new_min or not initialised:
            logger(f"Debug: Frame={frame} State={state}")
            state["mode"] = get_timer_mode(now)
            try:
                display.brightness = 1.0 if state["mode"] != "off" else 0.0
                draw(frame, now, state)
            except Exception as e:
                logger(f"Error: Draw Exception: {e}")

        frame += 1
        time.sleep(1)
        gc.collect()
except Exception as e:
    logger(f"Error: Fatal Exception: {e}")
    time.sleep(1)
    microcontroller.reset()
