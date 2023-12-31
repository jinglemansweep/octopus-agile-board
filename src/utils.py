import gc
import json
import math
import time
import adafruit_datetime as datetime
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_display_text.label import Label
from displayio import Group
from rtc import RTC

from constants import (
    DEBUG,
    NTP_TIMEZONE,
    OCTOPUS_API_URL,
    OCTOPUS_PRODUCT_CODE,
    OCTOPUS_RATE_LOW,
    OCTOPUS_RATE_HIGH,
    WEEKDAY_NAMES,
)

DATETIME_API = f"http://worldtimeapi.org/api/timezone/{NTP_TIMEZONE}"
OCTOPUS_TARIFF_CODE = f"E-1R-{OCTOPUS_PRODUCT_CODE}-A"
OCTOPUS_PERIOD_MINS = 30


def logger(msg, *args):
    _log_print("INFO", msg, *args)


def debug(msg, *args):
    global DEBUG
    if DEBUG:
        _log_print("DEBUG", msg, *args)


def _log_print(level, msg, *args):
    print(f"{level} [mem:{gc.mem_free()}] > {msg}", *args)


def matrix_rotation(accelerometer):
    return (
        int(
            (
                (
                    math.atan2(
                        -accelerometer.acceleration.y, -accelerometer.acceleration.x
                    )
                    + math.pi
                )
                / (math.pi * 2)
                + 0.875
            )
            * 4
        )
        % 4
    ) * 90


def fetch_json(requests, url):
    gc.collect()
    response = requests.get(url)
    return json.loads(response.text)


def set_current_time(requests):
    logger("Setting Time from Network")
    try:
        resp = fetch_json(requests, DATETIME_API)
        timestamp = resp["datetime"]
        logger(f"Time: {timestamp}")
        timetuple = parse_timestamp(resp["datetime"])
        RTC().datetime = timetuple
        gc.collect()
    except Exception as error:
        logger(f"Failed Network Time Fetch: {error}")


def get_current_and_next_agile_rates(
    requests, periods, period_size_mins=OCTOPUS_PERIOD_MINS
):
    now = datetime.datetime.now()
    rounded_minute = 0 if now.minute < 30 else 30
    period_from = now.replace(
        minute=rounded_minute, second=0, microsecond=0, tzinfo=None
    )
    period_to = period_from + datetime.timedelta(minutes=periods * period_size_mins)
    logger(
        f"Time Periods: Now={now.isoformat()} From={period_from.isoformat()} End={period_to.isoformat()}"
    )
    gc.collect()
    url = f"{OCTOPUS_API_URL}/v1/products/{OCTOPUS_PRODUCT_CODE}/electricity-tariffs/{OCTOPUS_TARIFF_CODE}/standard-unit-rates?period_from={period_from}&period_to={period_to}"
    resp = fetch_json(requests, url)
    sorted_data = sorted(resp["results"], key=lambda x: x["valid_from"])
    rates = []
    for r in sorted_data:
        dt_from = datetime.datetime.fromisoformat(
            r["valid_from"][:-1]
        ) + datetime.timedelta(hours=1)
        rates.append((dt_from.isoformat(), r["value_inc_vat"]))
    return rates


def find_lowest_contiguous_period(prices, periods):
    if periods > len(prices):
        return None  # Not enough data to find X hours
    min_period_start = 0
    min_period_end = periods - 1
    min_period_sum = sum(
        [price for _, price in prices[min_period_start : min_period_end + 1]]
    )
    current_sum = min_period_sum
    for i in range(periods, len(prices)):
        current_sum += prices[i][1] - prices[i - periods][1]
        if current_sum < min_period_sum:
            min_period_sum = current_sum
            min_period_start = i - periods + 1
            min_period_end = i
    return prices[min_period_start][0]


def get_new_epochs(ts_last=None):
    now = RTC().datetime
    ts = time.monotonic()
    if ts_last is None:
        return (ts, [True, True, True])
    epochs = [None, None, None]  # h, m, s
    if ts_last is None or ts > ts_last + 1:
        epochs[2] = True
        ts_last = ts
        if now.tm_sec == 0:
            epochs[1] = True
            if now.tm_min == 0:
                epochs[0] = True
    return (ts_last, epochs)


def build_date_fmt(now_tuple):
    return f"{now_tuple.tm_mday:02}/{now_tuple.tm_mon:02}"


def build_time_fmt(now_tuple):
    return f"{now_tuple.tm_hour:02}:{now_tuple.tm_min:02}"


def build_dow_fmt(now_tuple):
    return WEEKDAY_NAMES[now_tuple.tm_wday]


def parse_timestamp(timestamp, is_dst=-1):
    # 2022-11-04 21:46:57.174 308 5 +0000 UTC
    bits = timestamp.split("T")
    year_month_day = bits[0].split("-")
    hour_minute_second = bits[1].split(":")
    return time.struct_time(
        (
            int(year_month_day[0]),
            int(year_month_day[1]),
            int(year_month_day[2]),
            int(hour_minute_second[0]),
            int(hour_minute_second[1]),
            int(hour_minute_second[2].split(".")[0]),
            -1,
            -1,
            is_dst,
        )
    )


def rate_to_color(rate, low_color, high_color, default_color):
    if rate < OCTOPUS_RATE_LOW:
        return low_color
    elif rate > OCTOPUS_RATE_HIGH:
        return high_color
    else:
        return default_color


def color_brightness(color, brightness):
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    r = int(max(0, r * brightness))
    g = int(max(0, g * brightness))
    b = int(max(0, b * brightness))
    return (r << 16) | (g << 8) | b


def mqtt_connect(
    socket, network, broker, on_message_cb, port=1883, username=None, password=None
):
    MQTT.set_socket(socket, network._wifi.esp)
    client = MQTT.MQTT(broker=broker, port=port, username=username, password=password)
    client.on_connect = on_mqtt_connect
    client.on_disconnect = on_mqtt_disconnect
    client.on_message = on_message_cb
    client.connect()
    return client


async def mqtt_poll(client, timeout=1):
    while True:
        logger(f"MQTT POLL")
        try:
            client.loop(timeout=timeout)
        except Exception as error:
            # logger(f"mqtt poll error: error={error}")
            pass
        await asyncio.sleep(timeout)


def on_mqtt_connect(client, userdata, flags, rc):
    logger("MQTT: Connected: flags={} rc={}".format(flags, rc))


def on_mqtt_disconnect(client, userdata, rc):
    logger("MQTT: Disconnected: Reconnecting")
