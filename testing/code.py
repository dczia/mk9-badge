"""
MK9 Badge Hardware Tester

LED test: all 15 LEDs cycle red → green → blue.
  - Each color holds for 0.5 s, then a wipe sweeps the next color
    across in 0.5 s — 1 second total per color.
  - Tilt the badge on X or Y axis to change the wipe direction.

Key test: press any key to fast-flash that key's LED red → green → blue.
  Held keys are excluded from the background wipe until released.
  All 9 keys can be held simultaneously (NKRO test).

Accelerometer test: tilt X/Y changes the wipe direction live.
  X: negative = tilted left,   positive = tilted right
  Y: negative = top edge down, positive = bottom edge down
  Z: ignored
  The wipe always sweeps toward whichever edge is tilted down.
  Flat → keeps the last direction
"""

import board
import busio
import neopixel
import keypad
import time

# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------
NUM_PIXELS = 15

pixels = neopixel.NeoPixel(
    board.GP21, NUM_PIXELS,
    brightness=0.5,
    auto_write=False,
    pixel_order=neopixel.GRB,
)

row_pins = (board.GP27, board.GP26, board.GP16)
col_pins = (board.GP17, board.GP13, board.GP0)
keys = keypad.KeyMatrix(row_pins, col_pins, columns_to_anodes=True)

try:
    import adafruit_msa3xx
    _i2c = busio.I2C(board.GP19, board.GP18)
    sensor = adafruit_msa3xx.MSA301(_i2c)
    ACCEL_OK = True
except Exception:
    sensor = None
    ACCEL_OK = False

# ---------------------------------------------------------------------------
# Wipe groups — LED indices ordered by spatial position
#
# Key LED layout (index = row*3 + col):
#   0  1  2       col: 0.0  1.0  2.0
#   3  4  5       row: 0.0  1.0  2.0
#   6  7  8
#
# Backlight LED positions (row, col):
#   9  = (-0.7,  2.7)  top-right
#   10 = ( 1.0,  3.2)  right
#   11 = ( 2.7,  2.7)  bottom-right
#   12 = ( 2.7, -0.7)  bottom-left
#   13 = ( 1.0, -1.2)  left
#   14 = (-0.7, -0.7)  top-left
# ---------------------------------------------------------------------------
_WIPE = {
    'LR': [                     # left → right (col ascending)
        [13, 14, 12],           # left backlights
        [0, 3, 6],              # key col 0
        [1, 4, 7],              # key col 1
        [2, 5, 8],              # key col 2
        [9, 11, 10],            # right backlights
    ],
    'RL': [                     # right → left
        [9, 11, 10],
        [2, 5, 8],
        [1, 4, 7],
        [0, 3, 6],
        [13, 14, 12],
    ],
    'TB': [                     # top → bottom (row ascending)
        [9, 14],                # top backlights
        [0, 1, 2],              # key row 0
        [3, 4, 5, 10, 13],      # key row 1 + side backlights
        [6, 7, 8],              # key row 2
        [11, 12],               # bottom backlights
    ],
    'BT': [                     # bottom → top
        [11, 12],
        [6, 7, 8],
        [3, 4, 5, 10, 13],
        [0, 1, 2],
        [9, 14],
    ],
}

COLORS = [
    (255,   0,   0),   # red
    (  0, 255,   0),   # green
    (  0,   0, 255),   # blue
]

HOLD_TIME      = 0.5          # seconds each color is held solid
WIPE_STEP_TIME = 0.10         # 5 groups × 0.10 s = 0.5 s wipe
FLASH_HALF     = 0.05         # held-key R/G/B flash step time (50 ms/color)
ACCEL_DEAD     = 1.0          # m/s² — below this on both axes = "flat"

# Accelerometer-fault indicator: solid-fill flash, no wipe, all LEDs together.
ERROR_PATTERN = [
    COLORS[0], COLORS[0], COLORS[0], COLORS[2], COLORS[1],   # R R R B G
    COLORS[0], COLORS[0], COLORS[0], COLORS[2], COLORS[1],   # R R R B G
]
ERROR_STEP_TIME = 0.3          # seconds each color in ERROR_PATTERN is held

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
current_color = 0
next_color    = 1
wipe_dir      = 'LR'

# "hold" → all LEDs show current_color; "wipe" → sweeping next_color in
phase       = 'hold'
phase_start = time.monotonic()
wipe_step   = 0

# Per-LED colour buffer (modified as the wipe advances)
led_buf = [COLORS[current_color]] * NUM_PIXELS

key_held       = [False] * 9
key_flash_step = 0            # cycles through COLORS (R -> G -> B) while held
last_flash     = time.monotonic()

error_step       = 0
error_step_start = time.monotonic()
if not ACCEL_OK:
    led_buf = [ERROR_PATTERN[error_step]] * NUM_PIXELS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mark_accel_failed():
    """Sensor can't be read from / won't respond — switch to the error flash."""
    global ACCEL_OK, error_step, error_step_start
    ACCEL_OK          = False
    error_step        = 0
    error_step_start  = time.monotonic()


def _read_direction():
    """Return 'LR'/'RL'/'TB'/'BT' — wipe sweeps toward whichever edge is tilted
    down — or None if flat/unavailable."""
    if not ACCEL_OK:
        return None
    try:
        raw_x, raw_y, _ = sensor.acceleration
    except Exception:
        _mark_accel_failed()
        return None
    # Sensor is mounted rotated 90° relative to the board: its raw X axis
    # reads the board's top/bottom tilt, and its raw Y axis reads the
    # board's left/right tilt.
    ax, ay = raw_y, -raw_x
    if abs(ax) < ACCEL_DEAD and abs(ay) < ACCEL_DEAD:
        return None
    if abs(ax) >= abs(ay):
        # ax > 0: right edge down -> sweep ends at right (left-to-right)
        # ax < 0: left edge down  -> sweep ends at left  (right-to-left)
        return 'LR' if ax > 0 else 'RL'
    # ay > 0: bottom edge down -> sweep ends at bottom (top-to-bottom)
    # ay < 0: top edge down    -> sweep ends at top    (bottom-to-top)
    return 'TB' if ay > 0 else 'BT'


def _start_wipe():
    """Begin a new wipe: sample accel direction and reset wipe state."""
    global wipe_dir, wipe_step, phase, phase_start
    direction = _read_direction()
    if direction:
        wipe_dir = direction
    wipe_step   = 0
    phase       = 'wipe'
    phase_start = time.monotonic()


def _finish_wipe():
    """Wipe complete: advance colour cycle and enter hold phase."""
    global current_color, next_color, led_buf, phase, phase_start
    current_color = next_color
    next_color    = (next_color + 1) % len(COLORS)
    led_buf       = [COLORS[current_color]] * NUM_PIXELS
    phase         = 'hold'
    phase_start   = time.monotonic()


print("MK9 Badge Hardware Tester booted. Accelerometer OK: {}".format(ACCEL_OK))

# Prime display
pixels.fill(COLORS[current_color])
pixels.show()

last_accel_print = time.monotonic()

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    now = time.monotonic()

    # --- Phase logic ---
    if not ACCEL_OK:
        if now - error_step_start >= ERROR_STEP_TIME:
            error_step        = (error_step + 1) % len(ERROR_PATTERN)
            error_step_start  = now
            led_buf           = [ERROR_PATTERN[error_step]] * NUM_PIXELS

    elif phase == 'hold':
        if now - phase_start >= HOLD_TIME:
            _start_wipe()

    elif phase == 'wipe':
        elapsed_in_phase = now - phase_start
        target_step = int(elapsed_in_phase / WIPE_STEP_TIME)

        # Apply any new steps that are due
        while wipe_step <= target_step and wipe_step < len(_WIPE[wipe_dir]):
            for led in _WIPE[wipe_dir][wipe_step]:
                led_buf[led] = COLORS[next_color]
            wipe_step += 1

        if wipe_step >= len(_WIPE[wipe_dir]):
            _finish_wipe()

    # --- Key events ---
    event = keys.events.get()
    if event:
        if event.pressed:
            key_held[event.key_number] = True
            print("key {} down".format(event.key_number))
        elif event.released:
            key_held[event.key_number] = False
            print("key {} up".format(event.key_number))

    # --- Held-key R/G/B flash step ---
    if now - last_flash >= FLASH_HALF:
        key_flash_step = (key_flash_step + 1) % len(COLORS)
        last_flash     = now

    # --- 1 Hz accelerometer print ---
    if now - last_accel_print >= 1.0:
        last_accel_print = now
        if ACCEL_OK:
            try:
                raw_x, raw_y, az = sensor.acceleration
                ax, ay = raw_y, -raw_x  # board-relative: see _read_direction()
                print("accel: x={:.2f} y={:.2f} z={:.2f} m/s^2".format(ax, ay, az))
            except Exception as e:
                print("accel: read error: {}".format(e))
                _mark_accel_failed()
        else:
            print("accel: not available")

    # --- Render ---
    for i in range(NUM_PIXELS):
        pixels[i] = led_buf[i]

    # Overlay: held keys fast-flash R -> G -> B, excluded from the wipe
    for k in range(9):
        if key_held[k]:
            pixels[k] = COLORS[key_flash_step]

    pixels.show()
