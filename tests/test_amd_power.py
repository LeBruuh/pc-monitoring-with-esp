from pathlib import Path
import importlib.util
import json
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('cpu_v4',Path(__file__).parent.parent/'computer/cpu_sensors.py')
cpu=importlib.util.module_from_spec(spec);spec.loader.exec_module(cpu)

class AmdPowerTests(unittest.TestCase):
 def sample(self,name,value=75.5,now=1002):
  text=json.dumps({'updated_at_unix':1000,'cpu_temperature_c':55.6,'cpu_power_w':value,'power_sensor_name':name})
  with patch.object(Path,'read_text',return_value=text):return cpu.read_cpu_metrics('unused',now=now)
 def test_amd_package_is_in_total_and_wire_frame(self):
  metrics=self.sample('Package')
  self.assertEqual(metrics['power_w'],75.5)
  self.assertEqual(cpu.combined_power(metrics['power_w'],120),195.5)
  frame=cpu.build_frame(50,30,metrics,{'Power':120,'GPU Temp':40,'GPU Load':30,'VRAM Used':2048,'VRAM Total':16384})
  self.assertIn('CPUPower:75.5000;',frame);self.assertIn('Power:195.5000;',frame)
 def test_intel_package_still_accepted(self):self.assertEqual(self.sample('CPU Package')['power_w'],75.5)
 def test_no_core_double_count_or_estimate(self):
  for name in ('CPU Cores','Core #1 (SMU)','CPU PPT',None):self.assertIsNone(self.sample(name)['power_w'])
 def test_stale_or_missing_amd_power_stays_unavailable(self):
  self.assertIsNone(self.sample('Package',now=1011)['power_w'])
  self.assertIsNone(self.sample('Package',value=None)['power_w'])
 def test_read_retry_still_applies_to_amd(self):
  text=json.dumps({'updated_at_unix':1000,'cpu_temperature_c':55,'cpu_power_w':75.5,'power_sensor_name':'Package'})
  with patch.object(Path,'read_text',side_effect=[PermissionError(),text]),patch.object(cpu.time,'sleep'):
   self.assertEqual(cpu.read_cpu_metrics('unused',now=1002)['power_w'],75.5)

if __name__=='__main__':unittest.main()
