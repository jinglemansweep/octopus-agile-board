import gc

print("BOOT [mem:{}]".format(gc.mem_free()))

from displayio import release_displays

release_displays()

import app
