import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cpu_fix', Path(__file__).parent.parent / 'computer/cpu_sensors.py')
cpu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpu)
sample = json.dumps({'updated_at_unix': 1000, 'cpu_temperature_c': 68,
                     'cpu_power_w': 95, 'power_sensor_name': 'CPU Package'})

class SnapshotRetryTests(unittest.TestCase):
    def test_lock_then_fresh_measurement(self):
        with patch.object(Path, 'read_text', side_effect=[PermissionError(), sample]) as read, patch.object(cpu.time, 'sleep') as sleep:
            self.assertEqual(cpu.read_cpu_metrics('unused', now=1002), {'temperature_c': 68, 'power_w': 95})
            self.assertEqual(read.call_count, 2)
            sleep.assert_called_once_with(0.05)

    def test_permanent_lock_is_bounded(self):
        with patch.object(Path, 'read_text', side_effect=PermissionError()) as read, patch.object(cpu.time, 'sleep') as sleep:
            self.assertIsNone(cpu.read_cpu_metrics('unused', now=1002)['temperature_c'])
            self.assertEqual(read.call_count, 4)
            self.assertEqual(sleep.call_count, 3)

    def test_retry_does_not_accept_stale_measurements(self):
        with patch.object(Path, 'read_text', side_effect=[PermissionError(), sample]), patch.object(cpu.time, 'sleep'):
            self.assertIsNone(cpu.read_cpu_metrics('unused', now=1011)['temperature_c'])

    def test_missing_file_is_not_retried(self):
        with patch.object(Path, 'read_text', side_effect=FileNotFoundError()) as read, patch.object(cpu.time, 'sleep') as sleep:
            self.assertIsNone(cpu.read_cpu_metrics('unused', now=1002)['temperature_c'])
            read.assert_called_once()
            sleep.assert_not_called()

if __name__ == '__main__':
    unittest.main()
