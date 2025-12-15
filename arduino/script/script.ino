#include <TFT_eSPI.h>
#include "eevee72x72.h"
#include "esp32-hal.h"

TFT_eSPI tft = TFT_eSPI(); 

unsigned long lastUpdate = 0;
const unsigned long updateInterval = 5000;

int cpu = -1, ram = -1, gput = -1, gpul = -1, vram = -1, vramt = -1;
float power = -1;
bool validData;

#define RED_LED    13
#define YELLOW_LED 12
#define GREEN_LED  14

unsigned long lastPowerTime = 0;
float totalEnergy_Wh = 0.0;
const float pricePerKWh = 0.2985;

String serialLine = "";

unsigned long lastClockUpdate = 0;
String currentTime = "00:00:00";

String getLocalClock() {
  unsigned long seconds = millis() / 1000;

  int h = (seconds / 3600) % 24;
  int m = (seconds / 60) % 60;
  int s = seconds % 60;

  char buf[10];
  sprintf(buf, "%02d:%02d:%02d", h, m, s);
  return String(buf);
}

float getCPUTemp() {
  return temperatureRead();
}

void setup() {
  Serial.begin(115200);

  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setSwapBytes(true);
  tft.pushImage(124, 84, 72, 72, eevee72x72);
  
  pinMode(RED_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  
  digitalWrite(RED_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(GREEN_LED, LOW);
}

void loop() {

  if (Serial.available()) {
    serialLine = Serial.readStringUntil('\n');

    cpu   = parseValue(serialLine, "CPU");
    ram   = parseValue(serialLine, "RAM");
    gput  = parseValue(serialLine, "GPUTemp");
    gpul  = parseValue(serialLine, "GPULoad");
    vram  = parseValue(serialLine, "VRAMUsed");
    vramt = parseValue(serialLine, "VRAMTotal");
    power = parseFloatValue(serialLine, "Power");

    validData = !(cpu == -1 && ram == -1 && gpul == -1);
  }

  if (validData) {
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
  } else {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(GREEN_LED, LOW);
  }

  if (power > 0) {
    unsigned long now = millis();

    if (lastPowerTime > 0) {
      float deltaTimeSec = (now - lastPowerTime) / 1000.0;

      totalEnergy_Wh += (power * deltaTimeSec) / 3600.0;
    }

    lastPowerTime = now;
  }

  if (millis() - lastClockUpdate >= 1000) {
    currentTime = getLocalClock();
    lastClockUpdate = millis();
  }

  if (millis() - lastUpdate >= updateInterval) {
    lastUpdate = millis();
    if (validData) {
      tft.fillScreen(TFT_BLACK);
      drawStats(cpu, ram, gput, gpul, vram, vramt, power);
    }
  }
}

int parseValue(String line, String key) {
  int s = line.indexOf(key + ":");
  if (s < 0) return -1;
  int e = line.indexOf(";", s);
  if (e < 0) e = line.length();
  return line.substring(s + key.length() + 1, e).toInt();
}

float parseFloatValue(String line, String key) {
  int s = line.indexOf(key + ":");
  if (s < 0) return -1;
  int e = line.indexOf(";", s);
  if (e < 0) e = line.length();
  return line.substring(s + key.length() + 1, e).toFloat();
}

void drawStats(int cpu, int ram, int gput, int gpul, int vram, int vramt, float power) {
    tft.setTextSize(2);
    tft.setTextColor(TFT_WHITE);

    // CPU
    tft.setCursor(10, 10);
    tft.print("CPU: "); tft.print(cpu); tft.println("%");
    if(cpu > 80) drawBar(10, 35, cpu, TFT_RED);
    else if(cpu > 50) drawBar(10, 35, cpu, TFT_YELLOW);
    else drawBar(10, 35, cpu, TFT_GREEN);

    // RAM
    tft.setCursor(10, 60);
    tft.print("RAM: "); tft.print(ram); tft.println("%");
    if(ram > 85) drawBar(10, 85, ram, TFT_RED);
    else if(ram > 60) drawBar(10, 85, ram, TFT_YELLOW);
    else drawBar(10, 85, ram, TFT_GREEN);

    // GPU
    tft.setCursor(10, 110);
    tft.print("GPU: "); 
    tft.print(gpul); tft.print("%, ");
    tft.print(gput); 
    tft.setCursor(tft.getCursorX(), 105);
    tft.print("o");
    tft.setCursor(tft.getCursorX(), 110);
    tft.println("C");

    if(gpul > 85) drawBar(10, 135, gpul, TFT_RED);
    else if(gpul > 50) drawBar(10, 135, gpul, TFT_YELLOW);
    else drawBar(10, 135, gpul, TFT_GREEN);

    // VRAM + Power
    tft.setCursor(10, 165);
    tft.print("VRAM: ");
    tft.print(vram); tft.print("/"); tft.println(vramt);

    tft.setCursor(10, 185);
    tft.print("Power: "); tft.print(power); tft.print("W");

    float totalEnergy_kWh = totalEnergy_Wh / 1000.0;
    float costEuro = totalEnergy_kWh * pricePerKWh;

    tft.setCursor(10, 205);
    if (costEuro < 0.01) {
      tft.printf("ges. %.2f kWh, %.2f ct", totalEnergy_kWh, costEuro*100);
    } else {
      tft.printf("ges. %.2f kWh, %.2f EUR", totalEnergy_kWh, costEuro);
    }

    // Eevee Bild
    tft.pushImage(230, 35, 72, 72, eevee72x72);

    tft.setTextSize(1);

    // Uhrzeit
    tft.setCursor(230, 115);
    tft.print("Time: ");
    tft.print(currentTime);

    // ESP32-Temp
    tft.setCursor(230, 130);
    tft.print("ESP Temp: ");
    tft.print(getCPUTemp(), 1);
    tft.println(" C");
}

void drawBar(int x, int y, int value, uint16_t color) {
  tft.fillRect(x, y, 200, 15, TFT_DARKGREY);
  int w = map(value, 0, 100, 0, 200);
  tft.fillRect(x, y, w, 15, color);
}
