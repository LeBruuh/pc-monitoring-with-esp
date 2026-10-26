from pathlib import Path
import sys
import os
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'computer'))
if os.name=='nt':
 import eeveemonitoring as agent

@unittest.skipUnless(os.name=='nt','Windows agent')
class AgentSecurityTests(unittest.TestCase):
 def test_notification_uses_native_tray(self):
  tray=Mock();tray.HAS_NOTIFICATION=True
  with patch.object(agent,'TRAY_ICON',tray),patch.object(agent,'TRAY_READY') as ready:
   ready.is_set.return_value=True
   agent.notify('USB connected')
   tray.notify.assert_called_once_with('USB connected',agent.APP_NAME)
 def test_notification_waits_for_ready_tray(self):
  tray=Mock()
  with patch.object(agent,'TRAY_ICON',tray),patch.object(agent,'TRAY_READY') as ready:
   ready.is_set.return_value=False
   agent.notify('USB connected')
   tray.notify.assert_not_called()
 def test_gpu_command_uses_verified_absolute_path_without_shell(self):
  binary=Path('C:/Windows/System32/nvidia-smi.exe')
  with patch.object(agent,'nvidia_smi',return_value=binary),patch.object(agent.subprocess,'check_output',return_value='40, 50, 1024, 8192, 100.5') as command:
   self.assertEqual(agent.get_gpu_stats()['Power'],100.5)
   self.assertEqual(command.call_args.args[0][0],str(binary))
   self.assertFalse(command.call_args.kwargs.get('shell',False))
 def test_no_untrusted_fallback_when_nvidia_is_missing(self):
  with patch.object(agent,'nvidia_smi',return_value=None),patch.object(agent.subprocess,'check_output') as command:
   self.assertEqual(agent.get_gpu_stats()['Power'],-1)
   command.assert_not_called()

if __name__=='__main__':unittest.main()
