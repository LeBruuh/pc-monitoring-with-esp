# Third-party material

The original monitor is by LeBruuh and remains credited in [LICENSE](LICENSE) (MIT).

The animated Eevee artwork is from the PMDCollab SpriteCollab repository, species
0133, revision `a8275d343759dd01acd32fcb05134669c9df0b6a`. The supplied credit is
CHUNSOFT. The upstream attribution record and CC BY-NC 4.0 license are preserved
in [arduino/assets/eevee/sources](arduino/assets/eevee/sources).

`arduino/script/PetAssets.h`, the sprite PNGs, and their GIF previews are derived
from that artwork and carry its separate license. The root MIT license does not
replace the artwork license. `EventSleep`, `Idle`, and an accelerated `Walk`
cycle provide sleep, awake, and run modes. No new character artwork was drawn.
The source revision, frame timings, and file hashes are in
[manifest.json](arduino/assets/eevee/manifest.json).

LibreHardwareMonitor 0.9.6 (MPL-2.0), its Windows dependencies, and PawnIO are
external runtime components. Their binaries are not committed here. Obtain the
official releases and retain their accompanying licenses when distributing
a portable Windows build. TFT_eSPI 2.5.43 and the Espressif ESP32 3.3.12 core
are also installed as external build dependencies.
