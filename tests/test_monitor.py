import json
import math
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "computer"))
from cpu_sensors import build_frame, combined_power, read_cpu_metrics


class PowerTests(unittest.TestCase):
    def test_combined_measured_power_and_serial_frame(self):
        gpu = {"Power": 100.25, "GPU Temp": 40, "GPU Load": 10, "VRAM Used": 1000, "VRAM Total": 8192}
        frame = build_frame(20, 30, {"temperature_c": 55.2, "power_w": 25.5}, gpu)
        fields = dict(part.split(":", 1) for part in frame.strip().strip(";").split(";"))
        self.assertEqual(float(fields["Power"]), 125.75)
        self.assertEqual(float(fields["CPUPower"]), 25.5)
        self.assertEqual(float(fields["GPUPower"]), 100.25)
        self.assertTrue(frame.endswith(";\n"))

    def test_missing_or_invalid_component_never_becomes_zero_or_gpu_only(self):
        for bad in (None, -1, math.nan, math.inf, True, 1001):
            self.assertIsNone(combined_power(bad, 100))
            self.assertIsNone(combined_power(25, bad))
        self.assertEqual(combined_power(0, 0), 0)

    def test_atomic_fresh_snapshot_and_no_core_double_count(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cpu.json"
            path.write_text(json.dumps({"updated_at_unix": 1000, "cpu_temperature_c": 55.55,
                "cpu_power_w": 25.5, "power_sensor_name": "CPU Package",
                "power_sensors": [{"name": "CPU Cores", "value": 20}]}))
            self.assertEqual(read_cpu_metrics(path, now=1002), {"temperature_c": 55.5, "power_w": 25.5})
            self.assertIsNone(read_cpu_metrics(path, now=1011)["power_w"])
            self.assertIsNone(read_cpu_metrics(path, now=990)["power_w"])
            path.write_text('{"cpu_power_w":')
            self.assertIsNone(read_cpu_metrics(path, now=1002)["power_w"])

    def test_old_temperature_only_snapshot_is_not_a_power_measurement(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cpu.json"
            path.write_text(json.dumps({"updated_at_unix": 1000, "cpu_temperature_c": 50}))
            self.assertEqual(read_cpu_metrics(path, now=1002), {"temperature_c": 50, "power_w": None})

    def test_largest_serial_frame_fits_firmware_line_buffer(self):
        frame = build_frame(100, 100, {"temperature_c": 125, "power_w": 1000},
            {"Power": 1000, "GPU Temp": 125, "GPU Load": 100, "VRAM Used": 9999999, "VRAM Total": 9999999})
        self.assertLess(len(frame.encode()), 256)


class DisplayRegressionTests(unittest.TestCase):
    def test_dynamic_fields_never_overwrite_each_other(self):
        sketch = Path(__file__).resolve().parents[1] / "arduino/script/script.ino"
        text = sketch.read_text()
        fields = [tuple(map(int, match)) for match in re.findall(r"\bfield\((\d+),(\d+),(\d+),(\d+),(\d+),", text)]
        self.assertEqual(len(fields), 10)
        for i, (name, x, y, w, h) in enumerate(fields):
            self.assertLessEqual(x+w, 320)
            self.assertLessEqual(y+h, 240)
            for other, ox, oy, ow, oh in fields[i+1:]:
                intersects = x < ox+ow and ox < x+w and y < oy+oh and oy < y+h
                self.assertFalse(intersects, f"Fields {name} and {other} overlap")
        # The original 228px VRAM field intersected the lower half of ESP field 8.
        vram = next(f for f in fields if f[0] == 3)
        self.assertLessEqual(vram[1]+vram[3], 220)


if __name__ == '__main__':
    unittest.main()
