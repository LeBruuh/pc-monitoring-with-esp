"""Read one fresh CPU bridge snapshot and combine measured package/board power."""
from pathlib import Path
import json
import math
import time


def valid_number(value, lower, upper):
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) and lower <= value <= upper else None


def read_cpu_metrics(path, now=None, max_age=10):
    unavailable = {"temperature_c": None, "power_w": None}
    try:
        # Windows can briefly deny access while the sensor replaces its snapshot.
        # Retry only that transient read; stale or invalid samples stay unavailable.
        for attempt in range(4):
            try:
                snapshot = Path(path).read_text(encoding="utf-8-sig")
                break
            except OSError as error:
                if attempt == 3 or not (isinstance(error, PermissionError) or
                                        getattr(error, "winerror", None) in (5, 32, 33)):
                    raise
                time.sleep(0.05)
        sample = json.loads(snapshot)
        stamp = valid_number(sample.get("updated_at_unix"), 0, 1e12)
        if stamp is None or not -2 <= (time.time() if now is None else now) - stamp <= max_age:
            return unavailable
        temperature = valid_number(sample.get("cpu_temperature_c"), 0.01, 125)
        power = valid_number(sample.get("cpu_power_w"), 0, 1000)
        if sample.get("power_sensor_name") not in ("CPU Package", "Package"):
            power = None
        return {"temperature_c": round(temperature, 1) if temperature is not None else None,
                "power_w": power}
    except (OSError, ValueError, TypeError, AttributeError):
        return unavailable


def combined_power(cpu_w, gpu_w):
    cpu = valid_number(cpu_w, 0, 1000)
    gpu = valid_number(gpu_w, 0, 1000)
    return cpu + gpu if cpu is not None and gpu is not None else None


def build_frame(cpu_load, ram_usage, cpu, gpu):
    cpu_power = valid_number(cpu["power_w"], 0, 1000)
    gpu_power = valid_number(gpu["Power"], 0, 1000)
    total = combined_power(cpu_power, gpu_power)
    def wire(value):
        return f"{value:.4f}" if value is not None else "-1"
    return (
        f"CPU:{cpu_load};RAM:{ram_usage};CPUTemp:{wire(cpu['temperature_c'])};"
        f"GPUTemp:{gpu['GPU Temp']};GPULoad:{gpu['GPU Load']};"
        f"VRAMUsed:{gpu['VRAM Used']};VRAMTotal:{gpu['VRAM Total']};"
        f"CPUPower:{wire(cpu_power)};GPUPower:{wire(gpu_power)};Power:{wire(total)};\n"
    )
