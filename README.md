```
___  ____     _____  ______           _            
|  \/  | |   |  _  | | ___ \         | |           
| .  . | | __| |_| | | |_/ / __ _  __| | __ _  ___ 
| |\/| | |/ /\____ | | ___ \/ _` |/ _` |/ _` |/ _ \
| |  | |   < .___/ / | |_/ / (_| | (_| | (_| |  __/
\_|  |_/_|\_\\____/  \____/ \__,_|\__,_|\__, |\___|
                                         __/ |     
                                        |___/      
-------------------------------------------------
D C Z I A  ----------  2 0 2 6
```

DCZia Presents: The MK9 Badge

It blinks. It types. You can wear it around your neck and then set it on your desk and actually use it\*.

\* _Desk productivity not guaranteed. DCZia assumes no responsibility for keys accidentally sent during badge parties. Consult your keyboard layer documentation before operating heavy machinery._

---

## About

The **MK9** is a fully functional **3×3 mechanical macropad badge**. Nine real mechanical switches, per-key RGB lighting, ambient underglow, an accelerometer that actually does something interesting, SAO support, and CircuitPython firmware out of the box — all in a package sized to hang around your neck at DEF CON and survive the week.

---

## Specs

**Keys**
- 9× mechanical switches in a 3×3 grid — standard MX footprint, swap keycaps as you please
- Ships with translucent blue keycaps
- Full N-key rollover USB HID keyboard when plugged into a computer

**Lighting**
- 9× WS2812B per-key RGB LEDs — one under each switch
- 6× SK6812 side-firing LEDs — edge-mounted for ambient underglow out the sides

**Brains & Sensors**
- RP2040 microcontroller
- 3-axis accelerometer — tilt-reactive lighting, shake to change patterns
- 2× SAO connectors (standard 6-pin, I2C + 2 GPIO each) — expand with the badge add-on ecosystem

**Power & I/O**
- USB-C — power and data
- 3× AAA battery pack — run it untethered
- Power switch for battery mode
- Reset button + BOOTSEL button for easy firmware flashing

**Firmware**
- Ships with CircuitPython firmware
- QMK-compatible hardware — reflash and run it as a full QMK macropad

---

## What It Does Out of the Box

On boot: a rainbow diagonal wipe sweeps across the keys and backlights. Any keypress skips it.

Once running:
- Background light patterns cycle across all 15 LEDs — rainbow wave, breathing pulse, or sparkle
- Pressing a key sends a colour ripple expanding outward from that key through all the LEDs
- Tilt the badge to shift the colour palette; shake it to switch patterns
- Plug into a computer and it shows up as a numpad (7–9 / 4–6 / 1–3 layout)

---

## Repository

```
mk9-badge/
├── buildguide.md — badge assembly, flashing, and troubleshooting
├── hardware/   — KiCad design files, BOM, fabrication outputs
└── software/   — MicroPython firmware
```

- [Build Guide →](buildguide.md) — assembly, battery installation, flashing, and troubleshooting
- [Hardware →](hardware/README.md) — schematics, PCB layout, drill files, BOM
- [Software →](software/README.md) — firmware architecture, pinout, library requirements, flashing instructions

**Fabrication outputs**:
- [PCB layer plot](hardware/output/mk9-badge.pdf)
- [PTH drill map](hardware/output/mk9-badge-PTH-drl_map.pdf)
- [NPTH drill map](hardware/output/mk9-badge-NPTH-drl_map.pdf)

---

## Programming / Updating

The badge runs [CircuitPython](https://circuitpython.org). To update the firmware:

1. Hold **BOOTSEL** while plugging the badge into your computer — it mounts as `RPI-RP2`.
2. Drag the CircuitPython `.uf2` onto the drive. It reboots as `CIRCUITPY`.
3. Copy the `lib/` folder contents to `CIRCUITPY/lib/` (see [software/README.md](software/README.md) for the library list).
4. Copy all `.py` files from `software/` to the root of `CIRCUITPY`.

The badge restarts automatically. If it gets into a weird state, delete everything on `CIRCUITPY` and start fresh — it won't brick.

Want to run QMK instead? The hardware is fully compatible; QMK setup instructions will be posted separately.

**Recommended IDEs:** Visual Studio Code with the [CircuitPython extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python), or [Thonny](https://thonny.org). A Commodore 64 with a serial adapter also works but is left as an exercise for the reader.

---

## Open Source

DCZia is committed to open source hardware and software. All design files and firmware are publicly available.

- **Live CAD (OnShape):** [View the design](https://cad.onshape.com/documents/36884624fbe35c16a5af61a7/w/233227193d278274727a44c3/e/ea987b4b53c4648fa3dc84b6)


