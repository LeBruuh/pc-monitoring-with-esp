#include <TFT_eSPI.h>
#include "esp32-hal.h"
#include "MonitorLogic.h"
#include "PetAnimation.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

TFT_eSPI tft;
TFT_eSprite fieldSprite(&tft);
bool spriteReady = false;
TFT_eSprite petSprite(&tft);
Pet::Animator petAnimator;
bool petReady=false,petDemo=false;
uint32_t petLastMs=0,petFrames=0,petDrawMs=0,petDemoStart=0;
Pet::Mode petDisplayedMode=Pet::Waiting;
uint8_t petDisplayedFrame=255;
constexpr int RED_LED=13, YELLOW_LED=12, GREEN_LED=14;
struct Metrics {
  int cpu=-1, ram=-1, gpu=-1, vram=-1, vramTotal=-1;
  float cpuTemp=-1, gpuTemp=-1;
  double cpuWatts=-1, gpuWatts=-1, watts=-1;
} metrics;
Monitor::EnergyMeter energy;
Monitor::Severity currentLight=Monitor::NoData;
bool haveData=false, lastFresh=false;
uint32_t lastDataMs=0, lastAuxMs=0;
uint32_t fullClears=0, fieldPaints=0;
char lineBuffer[256];
size_t lineLength=0;
bool discardLine=false;
String previousFields[10];
struct BarCache { int width=0; uint16_t color=TFT_DARKGREY; };
static BarCache metricBars[3];

bool readNumber(const char* line,const char* key,double& value) {
  size_t keyLength=strlen(key);
  for(const char* field=line; *field;) {
    const char* end=strchr(field,';');
    if(!end) end=field+strlen(field);
    if(size_t(end-field)>keyLength+1 && strncmp(field,key,keyLength)==0 && field[keyLength]==':') {
      size_t length=end-field-keyLength-1;
      if(length>=24) return false;
      char text[24];memcpy(text,field+keyLength+1,length);text[length]=0;
      char* tail=nullptr;value=strtod(text,&tail);
      if(tail==text) return false;
      while(*tail && isspace((unsigned char)*tail)) ++tail;
      return *tail==0 && isfinite(value);
    }
    field=*end ? end+1 : end;
  }
  return false;
}
int readLoad(const char* line,const char* key) {
  double value;
  return readNumber(line,key,value) && value>=0 && value<=100 ? int(value) : -1;
}
int readMemory(const char* line,const char* key) {
  double value;
  return readNumber(line,key,value) && value>=0 && value<10000000 ? int(value) : -1;
}
float readTemp(const char* line,const char* key) {
  double value;
  return readNumber(line,key,value) && value>0 && value<150 ? float(value) : -1;
}
bool fresh(uint32_t now) {
  return haveData && uint32_t(now-lastDataMs)<Monitor::STALE_MS;
}
void lights(Monitor::Severity state) {
  if(state==currentLight) return;
  digitalWrite(RED_LED,state==Monitor::Red);
  digitalWrite(YELLOW_LED,state==Monitor::Yellow);
  digitalWrite(GREEN_LED,state==Monitor::Green);
  currentLight=state;
}
uint16_t loadColor(Monitor::Severity state) {
  return state==Monitor::Red ? TFT_RED : state==Monitor::Yellow ? TFT_YELLOW :
         state==Monitor::Green ? TFT_GREEN : TFT_DARKGREY;
}
void staticText(int x,int y,const char* text,int size=2) {
  tft.setTextSize(size);tft.setTextColor(TFT_WHITE,TFT_BLACK);tft.setCursor(x,y);tft.print(text);
}
void layout() {
  tft.fillScreen(TFT_BLACK);++fullClears; // The only full-screen clear.
  tft.setTextWrap(false,false);
  staticText(10,8,"CPU:");staticText(10,58,"RAM:");staticText(10,108,"GPU:");
  for(int i=0;i<3;i++) {
    tft.fillRect(10,34+i*50,200,12,TFT_DARKGREY);
    tft.drawRect(9,33+i*50,202,14,TFT_DARKGREY);
  }
  staticText(10,159,"VRAM:");
  staticText(10,187,"CPU+GPU",1);
  staticText(190,187,"E:",1);
  staticText(10,209,"D1 C+G",1);
  staticText(230,211,"CAD HT",1);
  staticText(10,229,"D1 0.07065 CAD/kWh HT - CPU+GPU",1);
  staticText(230,114,"Temps",1);
  staticText(230,142,"ESP",1);
}
Pet::Mode petMode(uint32_t now) {
  if(petDemo) {
    uint32_t elapsed=now-petDemoStart;
    if(elapsed<9000) return Pet::Mode(elapsed/3000);
    petDemo=false;
  }
  return Pet::Mode(currentLight);
}
void animatePet(uint32_t now,bool force=false) {
  if(!petReady) return;
  Pet::Mode mode=petMode(now);
  if(!force && mode==petDisplayedMode && uint32_t(now-petLastMs)<Pet::interval(mode)) return;
  Pet::Pose pose=petAnimator.tick(now,mode);
  if(!force && mode==petDisplayedMode && pose.frame==petDisplayedFrame) return;
  petLastMs=now;petDisplayedMode=mode;
  petDisplayedFrame=pose.frame;
  uint32_t started=millis();
  Pet::draw(petSprite,pose);
  petSprite.pushSprite(Pet::X,Pet::Y);
  petDrawMs=millis()-started;++petFrames;
}
void field(int index,int x,int y,int w,int h,const String& text,int size=2) {
  if(previousFields[index]==text) return;
  previousFields[index]=text;++fieldPaints;
  if(spriteReady) {
    fieldSprite.fillSprite(TFT_BLACK);
    fieldSprite.setTextSize(size);fieldSprite.setTextColor(TFT_WHITE,TFT_BLACK);
    fieldSprite.setCursor(0,0);fieldSprite.print(text);
    fieldSprite.pushSprite(x,y,0,0,w,h);
  } else {
    tft.fillRect(x,y,w,h,TFT_BLACK);
    staticText(x,y,text.c_str(),size);
  }
}
void bar(int index,int value) {
  int width=Monitor::validLoad(value) ? value*2 : 0;
  Monitor::Severity severity=Monitor::level(value,index==1?60:50,index==0?80:85);
  uint16_t color=loadColor(severity);
  BarCache& old=metricBars[index];
  int x=10,y=34+index*50;
  if(color!=old.color) {
    if(width) tft.fillRect(x,y,width,12,color);
    if(width<200) tft.fillRect(x+width,y,200-width,12,TFT_DARKGREY);
  } else if(width>old.width) {
    tft.fillRect(x+old.width,y,width-old.width,12,color);
  } else if(width<old.width) {
    tft.fillRect(x+width,y,old.width-width,12,TFT_DARKGREY);
  }
  old.width=width;old.color=color;
}
String percentAndTemp(int load,float temperature) {
  String result=Monitor::validLoad(load)?String(load)+"%":"--%";
  result+=" ";
  result+=temperature>0?String(temperature,1)+"C":"N/A";
  return result;
}
String memoryText(bool valid) {
  if(!valid || metrics.vram<0 || metrics.vramTotal<=0) return "N/A";
  String text=String(metrics.vram/1024.0,1)+"/"+String(metrics.vramTotal/1024.0,1)+" Go";
  // Keep larger cards within the 138px field at text size 2.
  if(text.length()>11) text=String(metrics.vram/1024.0,1)+"/"+String(metrics.vramTotal/1024.0,1)+"Go";
  if(text.length()>11)
    text=String(metrics.vram/1024.0,0)+"/"+String(metrics.vramTotal/1024.0,0)+"Go";
  return text;
}
void render(uint32_t now) {
  bool valid=fresh(now);
  int cpu=valid?metrics.cpu:-1, ram=valid?metrics.ram:-1, gpu=valid?metrics.gpu:-1;
  field(0,70,8,150,22,percentAndTemp(cpu,valid?metrics.cpuTemp:-1));
  field(1,70,58,150,22,Monitor::validLoad(ram)?String(ram)+"%":"--%");
  field(2,70,108,150,22,percentAndTemp(gpu,valid?metrics.gpuTemp:-1));
  bar(0,cpu);bar(1,ram);bar(2,gpu);
  // Keep VRAM entirely left of x=220; the ESP sidebar starts at x=230.
  field(3,82,159,138,18,memoryText(valid),2);
  field(4,70,183,110,22,valid && metrics.watts>=0?String(metrics.watts,1)+"W":"N/A");
  field(5,206,187,104,10,String(energy.wh/1000.0,4)+"kWh",1);
  field(6,70,205,150,22,String(energy.costCad(),4)+"$");
  char timeText[20];unsigned long seconds=millis()/1000;
  snprintf(timeText,sizeof(timeText),"%02lu:%02lu:%02lu",seconds/3600,(seconds/60)%60,seconds%60);
  field(7,230,126,80,10,String(timeText),1);
  float esp=temperatureRead();
  field(8,230,154,80,10,isfinite(esp) && esp>0 ? String(esp,1)+" C":"N/A",1);
  field(9,230,170,80,10,valid?"USB OK":"Attente USB",1);
  lastFresh=valid;
}
void status() {
  bool valid=fresh(millis());
  Serial.printf("DISPLAY;VRAM_FONT:2;VRAM_TEXT:%s;\n",memoryText(valid).c_str());
  lights(valid?Monitor::combined(metrics.cpu,metrics.ram,metrics.gpu):Monitor::NoData);
  Serial.printf("STATE;VERSION:6;ROTATION:%d;LED:%s;R:%d;Y:%d;G:%d;BL:%d;FRESH:%d;CPU:%d;RAM:%d;GPULoad:%d;CPUTemp:%.2f;GPUTemp:%.2f;CPUPower:%.4f;GPUPower:%.4f;Power:%.4f;ENERGY_Wh:%.8f;RATE:%.5f;COST_CAD:%.8f;FULL_CLEARS:%lu;FIELD_PAINTS:%lu;PET_READY:%d;PET_MODE:%s;PET_FRAMES:%lu;PET_MS:%lu;FREE_HEAP:%lu;\n",
    int(tft.getRotation()),Monitor::name(currentLight),digitalRead(RED_LED),digitalRead(YELLOW_LED),digitalRead(GREEN_LED),
    digitalRead(TFT_BL),valid,metrics.cpu,metrics.ram,metrics.gpu,metrics.cpuTemp,metrics.gpuTemp,
    metrics.cpuWatts,metrics.gpuWatts,metrics.watts,energy.wh,Monitor::CAD_PER_KWH,energy.costCad(),(unsigned long)fullClears,(unsigned long)fieldPaints,
    petReady,Pet::name(petDisplayedMode),(unsigned long)petFrames,(unsigned long)petDrawMs,(unsigned long)ESP.getFreeHeap());
}
void handleLine(const char* line) {
  if(strcmp(line,"@STATUS")==0) { status();return; }
  if(strcmp(line,"@PETDEMO")==0) {
    petDemo=true;petDemoStart=millis();
    Serial.println("PETDEMO:START;DURATION_MS:9000;");return;
  }
  if(strcmp(line,"@PETLIVE")==0) {
    petDemo=false;Serial.println("PETDEMO:STOP;");return;
  }
  if(strcmp(line,"@SELFTEST")==0) {
    int failed=Monitor::selfTest();
    int petFailed=Pet::selfTest();
    Serial.printf("SELFTEST:%s;FAILED:%d;PET_FAILED:%d;\n",failed || petFailed?"FAIL":"PASS",failed,petFailed);return;
  }
  Metrics next;
  next.cpu=readLoad(line,"CPU");next.ram=readLoad(line,"RAM");next.gpu=readLoad(line,"GPULoad");
  if(Monitor::combined(next.cpu,next.ram,next.gpu)==Monitor::NoData) return;
  next.cpuTemp=readTemp(line,"CPUTemp");next.gpuTemp=readTemp(line,"GPUTemp");
  next.vram=readMemory(line,"VRAMUsed");next.vramTotal=readMemory(line,"VRAMTotal");
  double watts;
  if(readNumber(line,"CPUPower",watts) && watts>=0 && watts<=1000) next.cpuWatts=watts;
  if(readNumber(line,"GPUPower",watts) && watts>=0 && watts<=1000) next.gpuWatts=watts;
  next.watts=Monitor::combinedWatts(next.cpuWatts,next.gpuWatts);
  uint32_t now=millis();
  energy.sample(now,next.watts);
  metrics=next;lastDataMs=now;haveData=true;
  lights(Monitor::combined(metrics.cpu,metrics.ram,metrics.gpu));
  render(now);
}
void setup() {
  Serial.begin(115200);
  pinMode(RED_LED,OUTPUT);pinMode(YELLOW_LED,OUTPUT);pinMode(GREEN_LED,OUTPUT);
  digitalWrite(RED_LED,LOW);digitalWrite(YELLOW_LED,LOW);digitalWrite(GREEN_LED,LOW);
  tft.init();tft.setRotation(3);
  fieldSprite.setColorDepth(16);
  spriteReady=fieldSprite.createSprite(230,22)!=nullptr;
  fieldSprite.setTextWrap(false,false);
  petSprite.setColorDepth(16);
  petReady=petSprite.createSprite(Pet::WIDTH,Pet::HEIGHT)!=nullptr;
  if(!petReady) {
    petSprite.setColorDepth(8);
    petReady=petSprite.createSprite(Pet::WIDTH,Pet::HEIGHT)!=nullptr;
  }
  petSprite.setTextWrap(false,false);
  layout();render(millis());
  animatePet(millis(),true);
  Serial.println("PCMON_READY;VERSION:6;ROTATION:3;BL:32;RATE:0.07065;SCOPE:CPU+GPU;PET:SPRITES;");
}
void loop() {
  while(Serial.available()) {
    char ch=char(Serial.read());
    if(ch=='\r') continue;
    if(ch=='\n') {
      if(!discardLine && lineLength) {lineBuffer[lineLength]=0;handleLine(lineBuffer);}
      lineLength=0;discardLine=false;
    } else if(!discardLine) {
      if(lineLength<sizeof(lineBuffer)-1) lineBuffer[lineLength++]=ch;
      else {lineLength=0;discardLine=true;}
    }
  }
  uint32_t now=millis();
  bool valid=fresh(now);
  lights(valid?Monitor::combined(metrics.cpu,metrics.ram,metrics.gpu):Monitor::NoData);
  if(uint32_t(now-lastAuxMs)>=1000 || valid!=lastFresh) {
    lastAuxMs=now;render(now);
  }
  animatePet(now);
  delay(1);
}
