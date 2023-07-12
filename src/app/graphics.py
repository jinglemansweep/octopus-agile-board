from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from displayio import Group

from app.constants import (
    COLOR_WHITE,
    COLOR_WHITE_DARK,
    COLOR_RED,
    COLOR_RED_DARK,
    COLOR_MAGENTA,
    COLOR_MAGENTA_DARK,
    COLOR_BLUE,
    COLOR_BLUE_DARK,
    COLOR_GREEN,
    COLOR_GREEN_DARK,
    COLOR_YELLOW,
    COLOR_YELLOW_DARK,
    COLOR_CYAN,
    COLOR_CYAN_DARK,
)


def rate_to_color(rate):
    if rate < 0.0:
        return COLOR_WHITE_DARK
    elif rate < 0.05:
        return COLOR_CYAN_DARK
    elif rate < 0.1:
        return COLOR_BLUE_DARK
    elif rate < 0.15:
        return COLOR_GREEN_DARK
    elif rate < 0.30:
        return COLOR_YELLOW_DARK
    else:
        return COLOR_RED_DARK


def make_box(
    x,
    y,
    width,
    height,
    font,
    text="",
    color=COLOR_WHITE_DARK,
    background_color=COLOR_RED_DARK,
    background_width=2,
    text_offset=2,
):
    inner_height = height - 1
    group = Group()
    background_rect = Rect(
        x=x, y=y, width=background_width, height=inner_height, fill=background_color
    )
    group.append(background_rect)
    group.append(
        Label(
            x=x + background_width + 1,
            y=y + text_offset,
            font=font,
            text=text,
            color=color,
        )
    )
    return group


class CellLabel(Label):
    def __init__(self, text, font, color=0x222222, x=0, y=0):
        super().__init__(x=x, y=y, text=text, color=color, font=font)
