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
from win10toast import ToastNotifier
import winreg
import sys

# ------------------------------------------------------------
# Hilfsfunktion für PyInstaller
# ------------------------------------------------------------
def resource_path(relative_path):
    """Gibt den Pfad zu einer Ressource zurück, auch nach OneFile-Build."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(relative_path)

# ------------------------------------------------------------
# Einstellungen
# ------------------------------------------------------------
BAUD = 115200
CHECK_INTERVAL = 3
SEARCH_TIMEOUT = 60
ICON_PATH = resource_path("assets/eevee-icon.png") # Tray-Icon
TOAST_ICON = resource_path("assets/eevee-icon.ico")
APP_NAME = "Eevee-Hardware-Monitor"

RUNNING = True
ser = None
controller_connected = False

toaster = ToastNotifier()


# ------------------------------------------------------------
# Autostart prüfen
# ------------------------------------------------------------
def is_autostart_enabled():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ
        )
        value, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


# ------------------------------------------------------------
# Autostart aktivieren
# ------------------------------------------------------------
def enable_autostart():
    script_path = Path(sys.executable).resolve()
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{script_path}"')
        winreg.CloseKey(key)
        print("[Autostart] aktiviert.")
    except Exception as e:
        print(f"[Autostart Fehler] {e}")


# ------------------------------------------------------------
# Autostart deaktivieren
# ------------------------------------------------------------
def disable_autostart():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        print("[Autostart] deaktiviert.")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[Autostart Fehler] {e}")


# ------------------------------------------------------------
# Mikrocontroller suchen
# ------------------------------------------------------------
def find_microcontroller():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        keywords = ["CH340", "CP210", "USB", "ESP", "ARDUINO"]
        if any(k in p.description.upper() for k in keywords):
            try:
                connection = serial.Serial(p.device, BAUD, timeout=1)
                time.sleep(2)
                return connection
            except:
                continue
    return None


# ------------------------------------------------------------
# GPU
# ------------------------------------------------------------
def get_gpu_stats():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw",
            "--format=csv,noheader,nounits"
        ], 
        encoding="utf-8",
        startupinfo=startupinfo
        )

        temp, util, mem_used, mem_total, power = output.strip().split(", ")

        return {
            "GPU Temp": int(temp),
            "GPU Load": int(util),
            "VRAM Used": int(mem_used),
            "VRAM Total": int(mem_total),
            "Power": float(power)
        }

    except:
        return {
            "GPU Temp": -1,
            "GPU Load": -1,
            "VRAM Used": -1,
            "VRAM Total": -1,
            "Power": -1
        }


# ------------------------------------------------------------
# Daten senden
# ------------------------------------------------------------
def send_stats():
    global ser
    if ser is None:
        return

    cpu_load = int(psutil.cpu_percent())
    ram_usage = int(psutil.virtual_memory().percent)
    gpu = get_gpu_stats()

    msg = (
        f"CPU:{cpu_load};RAM:{ram_usage};"
        f"GPUTemp:{gpu['GPU Temp']};GPULoad:{gpu['GPU Load']};"
        f"VRAMUsed:{gpu['VRAM Used']};VRAMTotal:{gpu['VRAM Total']};"
        f"Power:{gpu['Power']};\n"
    )

    try:
        ser.write(msg.encode("utf-8"))
        print(msg.encode("utf-8"))
    except:
        try: ser.close()
        except: pass
        ser = None


# ------------------------------------------------------------
# Serial Monitor Thread
# ------------------------------------------------------------
def serial_worker():
    global ser, controller_connected, RUNNING
    start_time = time.time()

    while RUNNING:
        ports = [p.device for p in serial.tools.list_ports.comports()]

        # Prüfen, ob der aktuelle Port noch vorhanden ist
        if ser:
            if ser.port not in ports:
                try: ser.close()
                except: pass
                ser = None
                controller_connected = False
                toaster.show_toast(APP_NAME, f'Der Mikrocontroller an Port {ser.port} wurde getrennt.', icon_path=TOAST_ICON, duration=4)

        # Wenn kein Serielport offen, nach Mikrocontroller suchen
        if ser is None:
            ser = find_microcontroller()
            if ser and not controller_connected:
                controller_connected = True
                toaster.show_toast(
                    APP_NAME,
                    f'Die Verbindung zum Microcontroller wurde an Port {ser.port} hergestellt.',
                    icon_path=TOAST_ICON,
                    duration=3
                )

            # Beim Start: abbrechen nach Timeout
            if (time.time() - start_time) > SEARCH_TIMEOUT and not controller_connected:
                toaster.show_toast(
                    APP_NAME,
                    "Es wurde schon eine Weile kein Microcontroller gefunden. Programm wird beendet.",
                    icon_path=TOAST_ICON,
                    duration=5
                )
                stop_program()
                return

        # Wenn verbunden → Werte senden
        if ser:
            send_stats()

        time.sleep(5)


# ------------------------------------------------------------
# Tray-Funktionen
# ------------------------------------------------------------
def stop_program(icon=None, item=None):
    global RUNNING, ser
    RUNNING = False
    if ser:
        try: ser.close()
        except: pass
    if icon:
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
            "Autostart deaktivieren" if is_autostart_enabled() else "Autostart aktivieren",
            toggle_autostart
        ),
        pystray.MenuItem("Eevee beenden", stop_program)
    )


def start_tray():
    icon = pystray.Icon(
        APP_NAME,
        load_icon(),
        menu=create_menu()
    )
    icon.run()


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":
    t = threading.Thread(target=serial_worker, daemon=True)
    t.start()
    start_tray()
