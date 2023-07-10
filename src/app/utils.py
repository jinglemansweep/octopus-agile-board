import gc
import json
import math
import time
import adafruit_requests as requests
from rtc import RTC

from app.constants import DEBUG, NTP_TIMEZONE, OCTOPUS_API_URL, OCTOPUS_PRODUCT_CODE

DATETIME_API = f"http://worldtimeapi.org/api/timezone/{NTP_TIMEZONE}"
OCTOPUS_TARIFF_CODE = f"E-1R-{OCTOPUS_PRODUCT_CODE}-C"


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


def fetch_json(url, retry_count=3):
    failures = 0
    response = None
    logger(f"json fetch: url={url} retry_count={retry_count}")
    while not response:
        try:
            response = requests.get(url)
            failures = 0
        except AssertionError as error:
            logger(f"fetch retrying: error={error}")
            failures += 1
            if failures >= retry_count:
                raise AssertionError("fetch error") from error
            continue
    gc.collect()
    return json.loads(response.text)


def set_current_time():
    logger("network time: fetching time")
    try:
        resp = fetch_json(DATETIME_API)
        timestamp = resp["datetime"]
        logger(f"network time: fetched timestamp={timestamp}")
        timetuple = parse_timestamp(resp["datetime"])
        RTC().datetime = timetuple
        gc.collect()
    except Exception as error:
        logger(f"network time fetch failed: error={error}")

def get_octopus_agile_rates(period_from, period_to):
    gc.collect()
    try:
        base_url = f"{OCTOPUS_API_URL}/v1/products/{OCTOPUS_PRODUCT_CODE}/electricity-tariffs/{OCTOPUS_TARIFF_CODE}"
        url = f"{base_url}/standard-unit-rates?period_from={period_from}&period_to={period_to}"
        logger(f"Octopus API: Get Agile Rates: url={url}")
        resp = fetch_json(url)
        gc.collect()
        return resp
    except Exception as error:
        logger(f"Octopus API: Failed: error={error}")
        

def get_new_epochs(ts_last=None):
    now = RTC().datetime
    ts = time.monotonic()
    if ts_last is None:
        return (ts, [True, True, True])
    epochs = [None, None, None]  # h, m, s
    if ts_last is None or ts > ts_last + 1:
        epochs[2] = True
        # logger(f"epoch: second")
        ts_last = ts
        if now.tm_sec == 0:
            epochs[1] = True
            logger(f"epoch: minute")
            if now.tm_min == 0:
                epochs[0] = True
                logger(f"epoch: hour")
    # logger(f"epochs: hour={epochs[0]} min={epochs[1]} sec={epochs[2]}")
    return (ts_last, epochs)


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


def rgb_dict_to_hex(color, brightness=255):
    r = int(color["r"] * (brightness / 255))
    g = int(color["g"] * (brightness / 255))
    b = int(color["b"] * (brightness / 255))
    return rgb2hex(r, g, b)


def rgb2hex(r, g, b):
    return (r << 16) + (g << 8) + b
