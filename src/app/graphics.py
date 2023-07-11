from adafruit_display_text.label import Label
from adafruit_display_shapes.rect import Rect
from displayio import Group
from terminalio import FONT

from app.constants import COLOR_WHITE_DARK, COLOR_RED_DARK


def make_box(
    x, y, width, height, text="", font=FONT, color=COLOR_WHITE_DARK, background_color=COLOR_RED_DARK, background_width=2
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
            y=y + 2,
            font=font,
            text=text,
            color=color,
        )
    )
    return group
