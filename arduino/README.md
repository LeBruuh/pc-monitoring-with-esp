# ESP32 firmware

Validated hardware: ESP32-WROOM / NodeMCU-32S and ILI9341 320×240 SPI TFT.

| Signal | GPIO |
| --- | --- |
| MISO | 19 |
| MOSI | 23 |
| SCLK | 18 |
| CS | 15 |
| DC | 2 |
| RESET | 4 |
| Backlight | 32 |
| Red / yellow / green LEDs | 13 / 12 / 14 |

This revision uses GPIO32 for TFT backlight control and rotation 3 for an
upside-down mounted landscape screen. Adjust wiring and `setRotation` for your
own mounting. The SPI clock is 27 MHz.

With Espressif ESP32 core 3.3.12 and TFT_eSPI 2.5.43 installed, run
`scripts/Build-Firmware.ps1`. Optional parameters select `-ArduinoCli`,
`-ConfigFile`, and `-BuildPath`. Build output goes to `build/firmware`.
For the Arduino IDE, copy the repository’s User_Setup.h into the installed
TFT_eSPI library configuration before compiling `script/script.ino`.

A first installation can be uploaded through Arduino IDE/CLI with its normal
bootloader and partition files. For an ESP32 already using this partition layout,
the application binary is flashed at 0x10000. Close the Windows monitoring agent
before flashing because it owns the USB serial port. Reopen it after uploading.
Firmware restarts reset the session energy counter.

The display renders only changed metric fields and sprite frames. VRAM stays
in the x82..219 field, away from the ESP sidebar at x230. It uses enlarged text,
used/total values in Go, and division by 1024 from NVIDIA’s MiB readings.

Serial diagnostics at 115200 baud:

- `@STATUS`: version, rotation, LED state, metrics, energy, display counters, and sprite state.
- `@SELFTEST`: package-energy integration, severity, rollover/gap handling, sprite geometry and timing.
- `@PETDEMO`: sleep/awake/run animation demonstration for nine seconds, then return to real load.
- `@PETLIVE`: cancel the demonstration.

Artwork provenance, the source sheets, previews, and manifest are under
`assets/eevee`. Run `python scripts/prepare_assets.py` from the repository to
rebuild PetAssets.h and the previews from the pinned source sheets.
