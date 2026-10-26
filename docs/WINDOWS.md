# Windows agent and CPU reader

## Run from source

Install Python 3.12 x64, the CP210x USB driver for the ESP32 USB bridge, NVIDIA
drivers with `nvidia-smi`, and [PawnIO](https://pawnio.eu/) for CPU sensor access.
Install PawnIO using its normal signed installer. The CPU reader needs elevated
hardware access; the tray application runs as the normal interactive user.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r computer/requirements-build.txt
```

`setuptools<81` is retained because win10toast imports `pkg_resources`.

Download and extract the official [LibreHardwareMonitor 0.9.6 Windows release](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/tag/v0.9.6).
Then build the CPU reader with the directory containing its DLLs:

```powershell
.\scripts\Build-CpuSensors.ps1 -LibreHardwareMonitorDir C:\Tools\LibreHardwareMonitor
.\computer\Installer_capteur_CPU.cmd
.\.venv\Scripts\python.exe .\computer\eeveemonitoring.py
```

The installer requests Windows elevation and creates the interactive logon task
`ESP32Monitor-CPU-Temperature`. Its process uses normal priority (task priority 4),
updates `computer/cpu-sensors.json` about every two seconds, and restarts on failure.
If it finds a task pointing to a different installation, it stops with an explanation.
Install from the intended permanent directory. Running the installer again restarts
the old reader before applying its new task settings.

Use the tray menu to enable startup at login. The shortcut targets the current
source interpreter or packaged executable. USB reconnection is automatic.

## Build the portable Windows application

After building the CPU reader:

```powershell
.\scripts\Build-Agent.ps1 -Python .\.venv\Scripts\python.exe
```

The complete application is in `dist/EeveeMonitor`. Keep `_internal` and `sensors`
with the executable. On another PC, extract the entire directory, install the
USB/PawnIO prerequisites, run `Installer_capteur_CPU.cmd`, and start `EeveeMonitor.exe`.
A packaged application does not require Python or Arduino on the target PC.

For an existing installation, quit the tray application and stop the scheduled
CPU task before replacing its files. Keep the same installation path, replace
all application files, run the CPU installer again, and restart the application.
Avoid leaving a second old agent running from another directory.

## Diagnostics

```powershell
.\.venv\Scripts\python.exe .\computer\eeveemonitoring.py --diagnose
.\dist\EeveeMonitor\EeveeMonitor.exe --diagnose-file .\diagnostic-agent.json
```

Diagnostics include the agent version, CPU temperature/package watts, NVIDIA
readings, combined watts, USB bridge ports, assets, and logon-startup state.
They do not open the serial port. The CPU snapshot also lists raw power sensors.
An Intel package uses the name `CPU Package`; a Ryzen package uses `Package`.
Only a single valid package sensor is accepted. Core readings are not added again.

`ESP32_MONITOR_PORT` or `--port` selects an explicit port when auto-detection is
unsuitable. `ESP32_SENSOR_FILE` selects a different CPU snapshot file.
CPU snapshots older than 10 seconds or more than two seconds in the future are
rejected. Read locks receive at most three 50 ms delays before returning unavailable.
Do not use old sensor JSON files as a live source.

The agent writes a rotating `logs/monitor.log` beside itself. These files and
sensor snapshots are local runtime state and are excluded from Git.
