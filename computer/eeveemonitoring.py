import time
import psutil
import subprocess
import serial
import serial.tools.list_ports
import threading
from datetime import datetime
from pathlib import Path
from PIL import Image
import pystray
import os
import json
import argparse
import logging
from logging.handlers import RotatingFileHandler
import sys
from cpu_sensors import read_cpu_metrics, combined_power, build_frame
from monitor_paths import default_sensor_file, nvidia_smi

# ------------------------------------------------------------
# Hilfsfunktion für PyInstaller
# ------------------------------------------------------------
def resource_path(relative_path):
    """Resolve assets independently of the launch working directory."""
    base = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parent
    return base / relative_path

# ------------------------------------------------------------
# Einstellungen
# ------------------------------------------------------------
BAUD = 115200
CHECK_INTERVAL = 3
PORT_HINT = os.environ.get("ESP32_MONITOR_PORT")
ICON_PATH = resource_path("assets/eevee-icon.png") # Tray-Icon
TOAST_ICON = resource_path("assets/eevee-icon.ico")
APP_NAME = "Eevee-Hardware-Monitor"
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
STARTUP_LINK = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup/Eevee-Hardware-Monitor.lnk"

CPU_SENSOR_FILE = Path(os.environ.get("ESP32_SENSOR_FILE") or default_sensor_file())
RUNNING = True
ser = None
controller_connected = False

TRAY_ICON = None
TRAY_READY = threading.Event()


# ------------------------------------------------------------
# Autostart prüfen
# ------------------------------------------------------------
def is_autostart_enabled():
    return STARTUP_LINK.is_file()


# ------------------------------------------------------------
# Autostart aktivieren
# ------------------------------------------------------------
def enable_autostart():
    try:
        import win32com.client
        shortcut = win32com.client.Dispatch("WScript.Shell").CreateShortCut(str(STARTUP_LINK))
        if getattr(sys, "frozen", False):
            shortcut.TargetPath = sys.executable
        else:
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            shortcut.TargetPath = str(pythonw if pythonw.exists() else Path(sys.executable))
            shortcut.Arguments = subprocess.list2cmdline([str(Path(__file__).resolve())])
        shortcut.WorkingDirectory = str(APP_DIR)
        shortcut.IconLocation = str(TOAST_ICON)
        shortcut.Save()
        logging.info("Demarrage automatique active")
    except Exception:
        logging.exception("Impossible d'activer le demarrage automatique")
        raise


# ------------------------------------------------------------
# Autostart deaktivieren
# ------------------------------------------------------------
def disable_autostart():
    STARTUP_LINK.unlink(missing_ok=True)
    logging.info("Demarrage automatique desactive")


# ------------------------------------------------------------
# Mikrocontroller suchen
# ------------------------------------------------------------
def find_microcontroller():
    for port in serial.tools.list_ports.comports():
        if PORT_HINT:
            matches = port.device.upper() == PORT_HINT.upper()
        else:
            matches = port.vid in (0x10C4, 0x1A86, 0x303A) or any(
                token in port.description.upper() for token in ("CH340", "CH343", "CP210", "ESP32")
            )
        if not matches:
            continue
        connection = None
        try:
            connection = serial.Serial(port.device, BAUD, timeout=1, write_timeout=2)
            time.sleep(2)
            return connection
        except (serial.SerialException, OSError):
            if connection is not None:
                connection.close()
            logging.debug("Port indisponible : %s", port.device, exc_info=True)
    return None


# ------------------------------------------------------------
# GPU
# ------------------------------------------------------------
def get_gpu_stats():
    empty = {"GPU Temp": -1, "GPU Load": -1, "VRAM Used": -1, "VRAM Total": -1, "Power": -1}
    try:
        executable = nvidia_smi()
        if executable is None:
            return empty
        output = subprocess.check_output([
            str(executable),
            "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw",
            "--format=csv,noheader,nounits"
        ], encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
        fields = [value.strip() for value in output.strip().splitlines()[0].split(",")]
        if len(fields) != 5:
            return empty
        result = {}
        for (key, fallback), value in zip(empty.items(), fields):
            try:
                result[key] = float(value) if key == "Power" else int(float(value))
            except ValueError:
                result[key] = fallback
        return result
    except (OSError, subprocess.SubprocessError, IndexError):
        logging.debug("Lecture NVIDIA indisponible", exc_info=True)
        return empty


# ------------------------------------------------------------
# Daten senden
# ------------------------------------------------------------
def send_stats():
    if ser is None:
        return
    cpu_load = int(psutil.cpu_percent())
    ram_usage = int(psutil.virtual_memory().percent)
    gpu = get_gpu_stats()
    cpu = read_cpu_metrics(CPU_SENSOR_FILE)
    message = build_frame(cpu_load, ram_usage, cpu, gpu)
    try:
        ser.write(message.encode("utf-8"))
    except (serial.SerialException, OSError):
        disconnect_controller()


# ------------------------------------------------------------
# Serial Monitor Thread
# ------------------------------------------------------------
def serial_worker():
    global ser, controller_connected
    # Wait indefinitely, including when the ESP32 is plugged in after login.
    while RUNNING:
        try:
            ports = {port.device for port in serial.tools.list_ports.comports()}
            if ser is not None and ser.port not in ports:
                disconnect_controller()
            if ser is None:
                ser = find_microcontroller()
                if ser is not None:
                    controller_connected = True
                    notify(f"ESP32 connecte sur {ser.port}")
            if ser is not None:
                send_stats()
        except Exception:
            logging.exception("Erreur dans le suivi USB ; nouvelle tentative")
            disconnect_controller()
        time.sleep(CHECK_INTERVAL)


# ------------------------------------------------------------
# Tray-Funktionen
# ------------------------------------------------------------
def stop_program(icon=None, item=None):
    global RUNNING
    RUNNING = False
    disconnect_controller(announce=False)
    if icon is not None:
        icon.stop()


def load_icon():
    return Image.open(ICON_PATH)


def reload_menu(icon):
    icon.menu = create_menu()
    icon.update_menu()


def toggle_autostart(icon, item):
    if is_autostart_enabled():
        disable_autostart()
    else:
        enable_autostart()
    reload_menu(icon)


def create_menu():
    return pystray.Menu(
        pystray.MenuItem(
            "Desactiver le demarrage automatique" if is_autostart_enabled() else "Activer le demarrage automatique",
            toggle_autostart
        ),
        pystray.MenuItem("Quitter le moniteur ESP32", stop_program)
    )


def start_tray():
    global TRAY_ICON
    icon = pystray.Icon(
        APP_NAME,
        load_icon(),
        menu=create_menu()
    )
    TRAY_ICON = icon
    def ready(tray):
        tray.visible = True
        TRAY_READY.set()
    try:
        icon.run(setup=ready)
    finally:
        TRAY_READY.clear()
        TRAY_ICON = None


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
def notify(message):
    logging.info(message)
    try:
        icon = TRAY_ICON
        if icon is not None and TRAY_READY.is_set() and icon.HAS_NOTIFICATION:
            icon.notify(message, APP_NAME)
    except Exception:
        logging.debug("Notification Windows indisponible", exc_info=True)


def disconnect_controller(announce=True):
    global ser, controller_connected
    previous = ser
    ser = None
    was_connected = controller_connected
    controller_connected = False
    if previous is not None:
        port = previous.port
        try:
            previous.close()
        except (OSError, serial.SerialException):
            pass
        if announce and was_connected:
            notify(f"ESP32 deconnecte de {port}. En attente du prochain branchement.")


def main():
    global PORT_HINT
    parser = argparse.ArgumentParser(description="Moniteur PC vers ESP32 par USB")
    parser.add_argument("--port", help="Port COM explicite, sinon detection automatique")
    parser.add_argument("--diagnose", action="store_true", help="Verifier les mesures sans ouvrir de port USB")
    parser.add_argument("--diagnose-file", type=Path, help="Ecrire le diagnostic JSON dans un fichier")
    args = parser.parse_args()
    PORT_HINT = args.port or PORT_HINT
    if args.diagnose or args.diagnose_file:
        cpu = read_cpu_metrics(CPU_SENSOR_FILE)
        gpu = get_gpu_stats()
        report = {
            "agent_version": 5,
            "cpu_sensor_file": str(CPU_SENSOR_FILE),
            "python": sys.version.split()[0],
            "cpu_percent": psutil.cpu_percent(interval=.2),
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_temperature_c": cpu["temperature_c"],
            "cpu_power_w": cpu["power_w"],
            "gpu": gpu,
            "combined_power_w": combined_power(cpu["power_w"], gpu["Power"]),
            "energy_scope": "CPU Package + GPU board",
            "serial_ports": [{"device": p.device, "description": p.description, "vid": p.vid, "pid": p.pid}
                             for p in serial.tools.list_ports.comports()],
            "assets_ok": ICON_PATH.is_file() and TOAST_ICON.is_file(),
            "autostart_enabled": is_autostart_enabled(),
        }
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.diagnose_file:
            args.diagnose_file.write_text(text, encoding="utf-8")
        if sys.stdout is not None:
            print(text)
        return
    import win32event
    import win32api
    import winerror
    mutex = win32event.CreateMutex(None, False, "Local\\EeveeHardwareMonitor")
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        win32api.CloseHandle(mutex)
        return
    try:
        logs = APP_DIR / "logs"
        logs.mkdir(exist_ok=True)
        handler = RotatingFileHandler(logs / "monitor.log", maxBytes=500000, backupCount=2, encoding="utf-8")
        logging.basicConfig(level=logging.INFO, handlers=[handler],
                            format="%(asctime)s %(levelname)s %(message)s")
        logging.info("Agent demarre ; en attente de l'ESP32")
        worker = threading.Thread(target=serial_worker, daemon=True)
        worker.start()
        start_tray()
    finally:
        stop_program()
        win32api.CloseHandle(mutex)


if __name__ == "__main__":
    main()
