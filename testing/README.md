# Hardware Tester

Self-contained hardware test fixture for the MK9 badge. Copy `code.py` to the root of `CIRCUITPY` (replacing the production firmware) to run the tests.

## What It Tests

### LEDs
All 15 LEDs (9 key + 6 backlight) cycle through **red → green → blue** continuously:
- Each color holds for **0.5 s**
- A directional wipe sweeps the next color across all LEDs over **0.5 s**
- Total: **1 second per color**

### Key Matrix
Press any key — its **LED fast-flashes red → green → blue** as long as the key is held, and is excluded from the background wipe until released. All 9 keys can be held simultaneously to verify N-key rollover. Every press/release is also logged to the serial console (`key N down` / `key N up`). Expected LED for each key:

```
key 0 (C0R0) → LED 0    key 1 (C1R0) → LED 1    key 2 (C2R0) → LED 2
key 3 (C0R1) → LED 3    key 4 (C1R1) → LED 4    key 5 (C2R1) → LED 5
key 6 (C0R2) → LED 6    key 7 (C1R2) → LED 7    key 8 (C2R2) → LED 8
```

### Accelerometer
The wipe always sweeps toward whichever edge is tilted down, decided when a new wipe starts:

| Axis reading | Meaning | Direction |
|------|-----------|-----------|
| X < 0 | Tilted left | Right → Left |
| X > 0 | Tilted right | Left → Right |
| Y < 0 | Top edge down | Bottom → Top |
| Y > 0 | Bottom edge down | Top → Bottom |
| Flat (both axes < 1 m/s²) | — | Holds last direction |

Tilt the badge and watch the wipe direction change on the next colour transition.

If the accelerometer library/sensor is missing at boot, or a read fails at runtime, the tester stops the colour-cycle test and instead flashes all LEDs solid **red, red, red, blue, green** (repeated) at 0.3 s/color, with no wipe, as a fault indicator.

### Serial Output
Connect a serial terminal to see:
- A boot message reporting whether the accelerometer initialized OK
- Accelerometer X/Y/Z readings printed once per second (or `accel: not available` if the sensor is down)
- `key N down` / `key N up` for every key press/release

## Libraries Required

Beyond CircuitPython built-ins (`board`, `busio`, `time`, `keypad`), copy these from the Adafruit CircuitPython Bundle into `lib/`:

| Library | Notes |
|---------|-------|
| `neopixel.mpy` | LED driver |
| `adafruit_msa3xx.mpy` | Accelerometer driver |
| `adafruit_bus_device/` | I2C helper — dependency of `adafruit_msa3xx` |
| `adafruit_register/` | Register access helper — dependency of `adafruit_msa3xx` |

If the accelerometer library is missing or the sensor doesn't respond, the tester falls back gracefully — LEDs and keys still work, but the LEDs switch to the red/red/red/blue/green fault-flash pattern described above instead of the normal colour cycle.

## Restoring Production Firmware

After testing, copy all files from `software/` back to the root of `CIRCUITPY` (including `boot.py`).
