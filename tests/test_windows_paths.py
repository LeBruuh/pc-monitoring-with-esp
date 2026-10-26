from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'computer'))
import monitor_paths

class WindowsPathTests(unittest.TestCase):
 def test_snapshot_stays_under_protected_runtime(self):
  with patch.object(monitor_paths,'program_files',return_value=Path('C:/ProtectedPrograms')):
   self.assertEqual(monitor_paths.default_sensor_file(),Path('C:/ProtectedPrograms/EeveeMonitor/CpuSensors/Data/cpu-sensors.json'))
 def test_nvidia_uses_os_system_directory(self):
  with patch.object(monitor_paths,'system_directory',return_value=Path('C:/System')),patch.object(monitor_paths,'program_files',return_value=Path('C:/Programs')),patch.object(Path,'is_file',return_value=True):
   self.assertEqual(monitor_paths.nvidia_smi(),Path('C:/System/nvidia-smi.exe'))
 def test_nvidia_legacy_location_is_still_absolute(self):
  with patch.object(monitor_paths,'system_directory',return_value=Path('C:/System')),patch.object(monitor_paths,'program_files',return_value=Path('C:/Programs')),patch.object(Path,'is_file',side_effect=[False,True]):
   self.assertEqual(monitor_paths.nvidia_smi(),Path('C:/Programs/NVIDIA Corporation/NVSMI/nvidia-smi.exe'))
 def test_no_fallback_to_cwd_or_path(self):
  with patch.object(monitor_paths,'system_directory',return_value=Path('C:/System')),patch.object(monitor_paths,'program_files',return_value=Path('C:/Programs')),patch.object(Path,'is_file',return_value=False):
   self.assertIsNone(monitor_paths.nvidia_smi())

if __name__=='__main__':unittest.main()
