import board
import gc
import terminalio
import time
import adafruit_datetime as datetime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
from adafruit_display_text.label import Label
from adafruit_lis3dh import LIS3DH_I2C
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from busio import I2C
from displayio import Group

FONT = terminalio.FONT

from app.constants import (
    DEBUG,
    MATRIX_WIDTH,
    MATRIX_HEIGHT,
    MATRIX_BIT_DEPTH,
    MATRIX_COLOR_ORDER,
)

from app.utils import logger, matrix_rotation, get_new_epochs, set_current_time, get_current_and_next_agile_rates

gc.collect()


# Local Classes

class CellLabel(Label):
    def __init__(self, text, color=0x222222, font=FONT, x=2, y=6):
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
splash_group = Group()
splash_group.append(Label(x=1, y=4, font=FONT, text="agileBoard", color=0x220022))

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
#rates = get_current_and_next_agile_rates()
#logger(f"Rates: {rates}")
    
# SCREEN
root_group = Group()
label_rate = CellLabel("Rate", 0x222222)
root_group.append(label_rate)
label_frame = CellLabel("Frame", 0x222222, x=48) 
root_group.append(label_frame)



# DRAW
def draw(state):
    global label_frame, label_rate
    label_frame.text = str(state["frame"])
    if "rates" in state:
        label_rate.text = f"{state['rates'][0][1]:,.02f}"
    logger(f"Draw: state={state}")


# STATE
state = dict(frame=0)


# APP STARTUP
def run():
    global state
    gc.collect()
    logger("Start Event Loop")
    display.show(root_group)
    while True:
        gc.collect()
        try:
            draw(state)
            if state["frame"] % 60 == 0:
                state["rates"] = get_current_and_next_agile_rates()
            state["frame"] += 1
        except Exception as e:
            print("EXCEPTION", e)
        time.sleep(1)


# STARTUP
run()
