# PC Monitoring with ESP32 and ILI9341 â€” revised edition

A Windows agent sends live CPU, RAM, NVIDIA GPU, temperature, VRAM, and measured
CPU + GPU power to an ESP32 with an ILI9341 320Ã—240 display.

This branch extends [LeBruuhâ€™s original project](https://github.com/LeBruuh/pc-monitoring-with-esp)
from commit `1af5058029be994158c38773e0039a9596303199`. The original MIT license
and author credit are preserved. Earlier setup instructions are archived in
[docs/UPSTREAM_README.md](docs/UPSTREAM_README.md).

## Changes in this branch

- CPU temperature through a local LibreHardwareMonitor/PawnIO reader.
- Measured CPU package + NVIDIA board power, with session energy and cost.
- Intel `CPU Package` and AMD `Package` power sensors; no core/package double counting.
- Administrator-protected CPU reader and read-only telemetry for the ordinary agent.
- Normal-priority sensor task, fresh-sample checks, and bounded retries for temporary Windows file locks.
- Automatic USB discovery, reconnect, tray controls, and optional logon startup.
- Partial display redraws, corrected VRAM/ESP-temperature overlap, and larger VRAM text always in Go (used/total, divided by 1024).
- Larger Eevee sprite animations: curled asleep for green, awake for yellow, running for red.
- Display rotation 3 (180Â° from the upstream landscape view) and GPIO32 backlight.

The Windows source reports agent version 5; the ESP32 reports firmware version 6.
They use the same semicolon-delimited serial protocol at 115200 baud.

## Windows setup and building

For existing installations, see [security migration](docs/SECURITY_CHANGES.md).

See [docs/WINDOWS.md](docs/WINDOWS.md) for source execution, building the CPU
reader and portable application, sensor-task installation, and diagnostics.
Python 3.12 was used for the validated Windows builds. NVIDIA `nvidia-smi`, the
CP210x USB driver, and PawnIO must be available on each monitored computer.
A GPU from another vendor requires a different GPU reader.

The ESP32 retains its firmware when moved between PCs. Each PC still needs
its own running Windows agent and CPU sensor task. Re-run the CPU installer
when changing installation locations or replacing the sensor reader.

## ESP32 setup and building

See [arduino/README.md](arduino/README.md). The validated combination is
ESP32 NodeMCU-32S, Espressif ESP32 core 3.3.12, and TFT_eSPI 2.5.43.
The pin map is in `arduino/libraries/TFT_eSPI/User_Setup.h`; status LEDs use
GPIO13 (red), GPIO12 (yellow), and GPIO14 (green).

```powershell
arduino-cli core install esp32:esp32@3.3.12
arduino-cli lib install "TFT_eSPI@2.5.43"
.\scripts\Build-Firmware.ps1
```

The build uses the repositoryâ€™s TFT setup explicitly, without replacing the
installed TFT_eSPI library configuration. Configure `tft.setRotation(...)`
in the sketch for a different physical screen mounting.

## Measurements and configuration

The total is CPU package watts plus GPU board watts. It excludes other hardware
and PSU losses. If either component is missing, invalid, or stale, total watts
are unavailable and energy integration pauses. No missing component becomes zero.
The energy counter resets on ESP32 restart and does not bill long data gaps.

The configured tariff is **0.07065 CAD/kWh before taxes**, retained from this
installation. Set `Monitor::CAD_PER_KWH` in `MonitorLogic.h` for your tariff;
this is a configurable example rather than a universal electricity price.
LED and animation severity is the highest of CPU, RAM, and GPU utilization.

## Tests

```powershell
python -m unittest discover -s tests -p "test_*.py"
.\scripts\Test-PowerSelection.ps1
.\scripts\Test-InstallSecurity.ps1
python .\scripts\prepare_assets.py
```

Python tests cover serial frames, package power selection, missing/stale data,
read retries, protected system paths, display rectangles, and sprite conversion.
PowerShell/C# tests check privileged installation ownership and ACL policy. Firmware commands
`@SELFTEST`, `@STATUS`, `@PETDEMO`, and `@PETLIVE` provide on-device checks.
Read [docs/VALIDATION.md](docs/VALIDATION.md) for the scope of hardware validation.

## Credits and artwork

Code changes extend the original MIT project. Sprite artwork has separate
attribution and license terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Animation sources, palette/frame metadata, and GIF previews are committed so the
sprite header can be rebuilt. Runtime logs, sensor snapshots, machine paths,
installed binaries, drivers, and firmware build products are not committed.
