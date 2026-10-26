"""Windows paths obtained from OS APIs, never the current directory or PATH."""
import ctypes
from pathlib import Path


def program_files():
    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 0x26, None, 0, buffer) != 0:
        raise OSError("Cannot locate Windows Program Files")
    return Path(buffer.value)


def system_directory():
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
    if not 0 < length < len(buffer):
        raise OSError("Cannot locate the Windows system directory")
    return Path(buffer.value)


def default_sensor_file():
    return program_files() / "EeveeMonitor" / "CpuSensors" / "Data" / "cpu-sensors.json"


def nvidia_smi():
    candidates = (system_directory() / "nvidia-smi.exe",
                  program_files() / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe")
    return next((path for path in candidates if path.is_file()), None)
