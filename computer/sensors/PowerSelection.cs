using System;

public static class PowerSelection {
 public static bool IsPackagePower(string name,float? watts) {
  return (String.Equals(name,"CPU Package",StringComparison.OrdinalIgnoreCase) ||
          String.Equals(name,"Package",StringComparison.OrdinalIgnoreCase)) &&
         watts.HasValue && !float.IsNaN(watts.Value) && !float.IsInfinity(watts.Value) &&
         watts.Value>=0 && watts.Value<=1000;
 }
}
