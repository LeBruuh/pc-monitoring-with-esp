#pragma once
#include <stdint.h>
#include <math.h>

namespace Monitor {
constexpr uint32_t STALE_MS = 15000;
constexpr double CAD_PER_KWH = 0.07065; // Hydro-Quebec tariff D, tier 1, 2026-04-01, before taxes.
enum Severity { NoData = -1, Green = 0, Yellow = 1, Red = 2 };
inline bool validLoad(int value) { return value >= 0 && value <= 100; }
inline Severity level(int value, int warning, int critical) {
  if (!validLoad(value)) return NoData;
  return value > critical ? Red : (value > warning ? Yellow : Green);
}
inline Severity combined(int cpu, int ram, int gpu) {
  Severity result = level(cpu,50,80);
  Severity r = level(ram,60,85), g = level(gpu,50,85);
  if (r > result) result = r;
  if (g > result) result = g;
  return result;
}
inline const char* name(Severity s) {
  return s == Red ? "RED" : s == Yellow ? "YELLOW" : s == Green ? "GREEN" : "OFF";
}
struct EnergyMeter {
  double wh = 0;
  double previousW = -1;
  uint32_t previousMs = 0;
  bool haveSample = false;
  void sample(uint32_t now, double watts) {
    bool valid = isfinite(watts) && watts >= 0 && watts <= 2000;
    if (haveSample && valid) {
      uint32_t elapsed = now - previousMs; // uint32 subtraction handles millis rollover.
      if (elapsed <= STALE_MS)
        wh += (previousW + watts) * 0.5 * double(elapsed) / 3600000.0;
    }
    previousMs = now;
    previousW = watts;
    haveSample = valid;
  }
  double costCad() const { return wh / 1000.0 * CAD_PER_KWH; }
};
inline double combinedWatts(double cpu, double gpu) {
  return isfinite(cpu) && isfinite(gpu) && cpu>=0 && cpu<=1000 && gpu>=0 && gpu<=1000 ? cpu+gpu : -1;
}
inline int selfTest() {
  if (level(50,50,80)!=Green || level(51,50,80)!=Yellow || level(80,50,80)!=Yellow || level(81,50,80)!=Red) return 1;
  if (combined(10,20,100)!=Red || combined(100,20,10)!=Red || combined(10,86,10)!=Red) return 2;
  if (combined(10,60,50)!=Green || combined(10,61,50)!=Yellow || combined(-1,-1,-1)!=NoData) return 3;
  if (level(101,50,80)!=NoData || combined(0,-1,-1)!=Green) return 4;
  EnergyMeter energy;
  energy.sample(0,100);
  for(uint32_t i=1;i<=1200;i++) energy.sample(i*3000,100);
  if (fabs(energy.wh-100)>0.00001 || fabs(energy.costCad()-0.007065)>0.0000001) return 5;
  double before=energy.wh;
  energy.sample(7200000,100); // A long outage must not be billed as measured energy.
  if (energy.wh!=before) return 6;
  energy.sample(7203000,-1);
  energy.sample(7206000,100);
  if (energy.wh!=before) return 7;
  EnergyMeter wrap;
  wrap.sample(0xFFFFFF00U,200);
  wrap.sample(uint32_t(0xFFFFFF00U+3000U),200);
  if(fabs(wrap.wh-1.0/6.0)>0.000001) return 8;
  if(fabs(combinedWatts(25.5,100.25)-125.75)>0.000001 || combinedWatts(-1,100)!=-1 ||
     combinedWatts(50,-1)!=-1 || combinedWatts(NAN,100)!=-1 || combinedWatts(0,0)!=0) return 9;
  EnergyMeter combinedEnergy;
  combinedEnergy.sample(0,combinedWatts(25,100));
  for(uint32_t i=1;i<=1200;i++) combinedEnergy.sample(i*3000,combinedWatts(25,100));
  if(fabs(combinedEnergy.wh-125)>0.00001 || fabs(combinedEnergy.costCad()-0.00883125)>0.0000001) return 10;
  return 0;
}
}
