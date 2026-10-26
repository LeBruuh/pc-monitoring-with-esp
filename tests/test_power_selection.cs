using System;
class PowerSelectionTests {
 static int Main() {
  string[] accepted={"CPU Package","Package","package","cpu package"};
  foreach(string name in accepted)
   if(!PowerSelection.IsPackagePower(name,75.5f) || !PowerSelection.IsPackagePower(name,0f)) return 1;
  foreach(string name in new string[]{"CPU Cores","Core #1 (SMU)","CPU PPT","SoC",null,""})
   if(PowerSelection.IsPackagePower(name,75.5f)) return 2;
  foreach(float? value in new float?[]{null,-1f,float.NaN,float.PositiveInfinity,1001f})
   if(PowerSelection.IsPackagePower("Package",value)) return 3;
  Console.WriteLine("PASS: Intel and AMD package power; core, invalid and missing readings rejected.");
  return 0;
 }
}
