# pc-monitoring-with-esp

I build a computer monitoring program which shows you cpu, ram and gpu usage, gpu temperature, vram usage and currently used power. Additionally, it calculates the overall used power and how much your session (from connecting the program to your esp) aprox. costed.
The application shows different colors which indicate if one component is at a critical value.

Following I describe which components I used (with links, as of 01. Dec 2025) and how I used them. You can download all code and recreate this project.

Have fun :)


## Disclaimer
I am an absolute beginner and this is one of my first mini-projects. With that said, many things can be wrong or underperforming.
Feel free to [contact me](https://discord.gg/phD7Wzf2) to tell me what to change or improve.

## Components
I used following components. The prices are from 1. December 2025.

- [micro controller](https://amzn.eu/d/e7BkkHr), 6,99 €
- [traffic light leds](https://amzn.eu/d/hFKLvPI), 5,59 €
- [LAFVIN 3.2 inch TFT LCD Touch Display (320x240 px)](https://amzn.eu/d/9bgEoQS), 15,99 €
- [jumper cable](https://amzn.eu/d/e8eDK16), 5,94 €
- [bread boards](https://amzn.eu/d/4nmU4Gx), (you need only one), 7,64 €

- Overall price: 42,15 €

## Arduino
TODO: intro

### Wiring
The first important step is to wire the arduino correctly. Especially the screen is a little complicated but nothing to worry about. Secondly, I added a traffic light to determine if the arduino received valid data.

#### ILI9341-Touchscreen
TODO: Foto
TODO: Wiring

#### Status Light
TODO: Foto
TODO: Wiring

