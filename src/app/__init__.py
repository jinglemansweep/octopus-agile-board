import asyncio
import board
import gc
import os
import time
import adafruit_datetime as datetime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_matrixportal.network import Network
from displayio import Group

from app.constants import (
    DEBUG,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
    MATRIX_BIT_DEPTH,
    MATRIX_COLOR_ORDER,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_PREFIX,
    COLORS_RAINBOW,
    COLOR_RED_DARK,
    COLOR_BLUE_DARK,
    COLOR_GREEN_DARK,
    COLOR_MAGENTA_DARK,
    COLOR_YELLOW_DARK,
    COLOR_WHITE_DARK,
)
from app.graphics import CellLabel, make_box, rate_to_color
from app.utils import (
    logger,
    matrix_rotation,
    get_new_epochs,
    set_current_time,
    get_current_and_next_agile_rates,
    build_splash_group,
    build_date_fmt,
    build_time_fmt,
    mqtt_connect,
    mqtt_poll
)

from secrets import secrets

logger(
    f"Config: debug={DEBUG} matrix_width={MATRIX_WIDTH} matrix_height={MATRIX_HEIGHT}"
)

gc.collect()

# RGB MATRIX
logger("Configuring RGB Matrix")
from adafruit_matrixportal.matrix import Matrix
matrix = Matrix(
    width=MATRIX_WIDTH,
    height=MATRIX_HEIGHT,
    bit_depth=MATRIX_BIT_DEPTH,
    color_order=MATRIX_COLOR_ORDER,
)
gc.collect()

# ACCELEROMETER
from busio import I2C
from adafruit_lis3dh import LIS3DH_I2C
accelerometer = LIS3DH_I2C(I2C(board.SCL, board.SDA), address=0x19)
_ = accelerometer.acceleration  # drain startup readings
gc.collect()

# DISPLAY / FRAMEBUFFER
logger("Configuring Display")
display = matrix.display
display.rotation = matrix_rotation(accelerometer)
del accelerometer
gc.collect()

# STATIC RESOURCES
FONT = bitmap_font.load_font("assets/bitocra7.bdf")
gc.collect()

# SPLASH - DO NOT ENABLE - USES FAR TO MUCH RAM
#splash_group = build_splash_group(FONT, "jinglemansweep", COLORS_RAINBOW)
#display.show(splash_group)

# NETWORKING
logger("Configuring Networking")
network = Network(status_neopixel=None, debug=DEBUG)
network.connect()
gc.collect()
mac = network._wifi.esp.MAC_address
host_id = "{:02x}{:02x}{:02x}{:02x}".format(mac[0], mac[1], mac[2], mac[3])
requests = network.requests
logger(f"Host ID: {host_id}")

# MQTT
logger("Configuring MQTT")
MQTT_MESSAGES = []
def on_mqtt_message(client, topic, message):
    MQTT_MESSAGES.append((topic, message))
    logger(f"MQTT: Message: Topic={topic} Message={message}")
mqtt = mqtt_connect(socket, network, MQTT_BROKER, on_mqtt_message, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD)
mqtt.subscribe(f"{MQTT_TOPIC_PREFIX}/#")
mqtt.publish(f"{MQTT_TOPIC_PREFIX}/alive", "OK") # IMPORTANT
gc.collect()

# TIME
set_current_time(requests)
gc.collect()

# SCREEN
root_group = Group()

# SPRITE: BORDER
border_pos = (0, 0)
border_size = (MATRIX_WIDTH, MATRIX_HEIGHT)
border_width = 2
border_rect = RoundRect(
    border_pos[0],
    border_pos[1],
    border_size[0],
    border_size[1],
    r=1,
    outline=COLOR_BLUE_DARK,
    stroke=border_width,
)
root_group.append(border_rect)

# SPRITE: DATE
date_pos = (3, 5)
date_label = Label(
    x=date_pos[0],
    y=date_pos[1],
    font=FONT,
    text="DD/MM",
    color=COLOR_WHITE_DARK,
)
root_group.append(date_label)

# SPRITE: TIME
time_pos = (42, 5)
time_label = Label(
    x=time_pos[0],
    y=time_pos[1],
    font=FONT,
    text="HH:MM",
    color=COLOR_YELLOW_DARK,
)
root_group.append(time_label)

# SPRITE: DEBUG (FREE MEMORY)
# Mem Free
memfree_pos = (3, 26)
memfree_label = Label(
    x=memfree_pos[0],
    y=memfree_pos[1],
    font=FONT,
    text="0",
    color=COLOR_MAGENTA_DARK,
)
root_group.append(memfree_label)

# SPRITE: RATE NOW
ratenow_pos = (8, 14)
ratenow_label = Label(
    x=ratenow_pos[0],
    y=ratenow_pos[1],
    font=FONT,
    text="0",
    color=COLOR_WHITE_DARK,
)
root_group.append(ratenow_label)

# SPRITE: RATE NEXT
ratenext_pos = (45, 14)
ratenext_label = Label(
    x=ratenext_pos[0],
    y=ratenext_pos[1],
    font=FONT,
    text="0",
    color=COLOR_WHITE_DARK,
)
root_group.append(ratenext_label)

display.show(root_group)
#del splash_group
gc.collect()

# DRAW
def draw(frame, now, state):
    date_label.text = build_date_fmt(now)
    time_label.text = build_time_fmt(now)
    memfree_label.text = str(gc.mem_free())
    if "rates" in state:
        rate_now, rate_next = state["rates"][0][1], state["rates"][1][1]
        ratenow_label.text = f"{int(rate_now*100)}p"
        ratenext_label.text = f"{int(rate_next*100)}p"
        border_rect.outline = rate_to_color(rate_now)

# EVENTS
def handle_messages(state):
    global MQTT_MESSAGES
    while len(MQTT_MESSAGES) > 0:
        msg = MQTT_MESSAGES.pop(0)
        print(msg)
    return state

# STATE
frame = 0
state = dict()


# APP LOGIC
async def run():
    global mqtt, frame, state
    logger("Start Event Loop")
    initialised = False
    ts = time.monotonic()
    asyncio.create_task(mqtt_poll(mqtt))

    while True:
        now = datetime.datetime.now().timetuple()
        ts, (new_hour, new_min, new_sec) = get_new_epochs(ts)
        if (new_min and now.tm_min % 15 == 0) or not initialised:
            state["rates"] = get_current_and_next_agile_rates(requests)
            logger(f"Fetch: Rates={state['rates']}")
            initialised = True
        state = handle_messages(state)            
        try:
            draw(frame, now, state)
        except Exception as e:
            print("EXCEPTION", e)
        if new_min:
            logger(f"Debug: Frame={frame} State={state}")

        frame += 1
        await asyncio.sleep(0.1)
        gc.collect()


# STARTUP
while True:
    try:
        asyncio.run(run())
    except Exception as e:
        print("EXCEPTION", e)
    finally:
        logger(f"asyncio restarting")
        time.sleep(1)
        asyncio.new_event_loop()
