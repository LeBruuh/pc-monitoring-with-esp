# PC Monitoring with ESP32 and ILI9341

## 1. Overview
### What does this project do?
This project implements a pc monitoring application. It shows component usages of CPU, GPU and your electricity usage.

### Why does it exist?
I am a student in my final year of bachelor studies. I wanted to build a little project to level up my skills and share my work with you. Secondly, I would appreciate you to leave feedback and optimize my project.

### Supported platforms
I used Windows to build and run my application. It is required to have a NVIDIA GPU, because of the program's structure. Other combinations weren't tested.

## 2. Showcase
- Photos of the finished build

## 3. Features
This project provides the following key features:

Displayed metrics: Monitors your PC’s CPU, RAM, and GPU usage, GPU temperature, VRAM usage, and current power consumption in real time.

Color & LED status logic: The display and the traffic light LEDs indicate normal, warning, and critical states for each component.

Session cost calculation: Estimates the power consumption and approximate cost of your session from the moment you connect the program to the ESP32.

## 5. Components

### 5 What to Buy

- [micro controller](https://amzn.eu/d/e7BkkHr), 6,99 €
- [traffic light leds](https://amzn.eu/d/hFKLvPI), 5,59 €
- [LAFVIN 3.2 inch TFT LCD Touch Display (320x240 px)](https://amzn.eu/d/9bgEoQS), 15,99 €
- [jumper cable](https://amzn.eu/d/e8eDK16), 5,94 €
- [bread boards](https://amzn.eu/d/4nmU4Gx), (you need only one), 7,64 €

- Overall price: 42,15 € (as of 1. December 2025)

## 6. Project Structure
- Repository layout

## 7. Arduino / ESP32 Setup

### 7.1 Requirements
Before you start programming the ESP32, make sure you have the following set up:

Arduino IDE: Install the latest version from the official Arduino website.

Board Selection: Make sure the NodeMCU-32S (or your ESP32 variant) is correctly installed in the Arduino IDE. You also need to select the correct board and port before uploading any sketches.

### 7.2 Wiring

#### 7.2.1 ILI9341 Touchscreen

<p align="center">
  <img src="showcase/arduino-cables.jpeg" width="45%">
  <img src="showcase/ili-cables.jpeg" width="45%">
</p>

| ILI9341 Pin | ESP32 Pin | Description        |
|------------|-----------|--------------------|
| SDO (MISO) | D19       | SPI data from LCD  |
| SDI (MOSI) | D23       | SPI data to LCD    |
| SCK        | D18       | SPI clock          |
| CS         | D15       | Chip select        |
| DC         | D2        | Data / Command     |
| RESET      | D4        | Display reset      |
| LED        | 3V3       | Backlight power    |
| VCC        | 3V3       | Power supply       |
| GND        | GND       | Ground             |



#### 7.2.2 Status / Traffic Light LEDs

| Status Light Pin | ESP32 Pin | Meaning              |
|-----------------|-----------|----------------------|
| GND             | GND       | Ground               |
| R (Red)         | D13       | Critical value       |
| Y (Yellow)      | D12       | Warning / high load  |
| G (Green)       | D14       | Normal operation     |

### 7.3 Libraries
- Required libraries
- Installation steps
- User_Setup.h changes

### 7.4 Arduino Script
- Configuration options
- Important constants
- Customization tips

### 7.5 Uploading the Sketch
- Board & port selection
- Common problems

## 8. PC Application Setup

### 8.1 Requirements
- Python version
- Virtual environment (optional)
- Required permissions

### 8.2 Installation
- Create venv (optional)
- Install dependencies
- Configuration

### 8.3 Running the Application
- Start command
- Expected output
- First connection to ESP32

## 9. Usage
- Normal workflow
- Interpreting values
- LED & color meanings

## 10. Casing
coming soon ...

## 11. Known Issues
- White screen issue
- Serial reconnect problems
- Workarounds

## 12. Improvements & Roadmap
- Planned features
- Possible extensions

## 13. Disclaimer
This project is a beginner project and one of my first mini-projects.
Therefore, parts of the code or hardware setup may be inefficient, incomplete, or incorrect.

I did not actively search for vulnerabilities. As a result, unexpected behavior or side effects may occur.

I do not take responsibility for any damage, data loss, hardware issues, or other negative effects caused by using this project.
Use it at your own risk.

If you have suggestions, improvements, or feedback, feel free to [contact me](https://discord.gg/phD7Wzf2).

## 14. License
This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute this project, provided that the original copyright
notice and license text are included.

See the [LICENSE](LICENSE) file for more information.

## 15. Contact & Feedback
If you have questions, suggestions, or feedback, feel free to reach out:

Discord: [Join here](https://discord.gg/phD7Wzf2)
Contributions: Pull requests are welcome!

We appreciate any help to improve this project, fix bugs, or add new features.
