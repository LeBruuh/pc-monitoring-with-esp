#pragma once
#include <stdint.h>
#include "PetAssets.h"

namespace Pet {
constexpr int X=222, Y=2, WIDTH=98, HEIGHT=108, SCALE=3, FLOOR_Y=97;
enum Mode { Waiting=-1, Calm=0, Play=1, Hype=2 };
inline const char* name(Mode mode) {
  return mode==Hype?"RUN":mode==Play?"AWAKE":mode==Calm?"SLEEP":"WAIT";
}
inline const PetAssets::Clip& clipFor(Mode mode) {
  return mode==Hype?PetAssets::Run:mode==Play?PetAssets::Awake:PetAssets::Sleep;
}
inline uint32_t interval(Mode) { return 16; }
inline uint8_t frameAt(const PetAssets::Clip& clip,uint32_t elapsed) {
  uint32_t cycle=0;
  for(int i=0;i<clip.frames;i++) cycle+=clip.durations[i];
  if(!cycle) return 0;
  uint32_t position=elapsed%cycle;
  for(int i=0;i<clip.frames;i++) {
    if(position<clip.durations[i]) return uint8_t(i);
    position-=clip.durations[i];
  }
  return 0;
}
struct Pose { const PetAssets::Clip* clip; uint8_t frame; Mode mode; };
class Animator {
  Mode previous=Waiting;
  uint32_t startMs=0;
  bool started=false;
public:
  Pose tick(uint32_t now,Mode mode) {
    if(!started || mode!=previous) {startMs=now;previous=mode;started=true;}
    const PetAssets::Clip& clip=clipFor(mode);
    return Pose{&clip,mode==Waiting?uint8_t(0):frameAt(clip,uint32_t(now-startMs)),mode};
  }
};
template<class Surface>
void draw(Surface& surface,const Pose& pose) {
  surface.fillSprite(0);
  const PetAssets::Clip& clip=*pose.clip;
  int left=(WIDTH-clip.width*SCALE)/2,top=FLOOR_Y-clip.height*SCALE;
  const uint8_t* frame=clip.pixels+uint32_t(pose.frame)*clip.width*clip.height;
  for(int y=0;y<clip.height;y++) for(int x=0;x<clip.width;x++) {
    uint8_t color=frame[y*clip.width+x];
    if(color) surface.fillRect(left+x*SCALE,top+y*SCALE,SCALE,SCALE,PetAssets::palette[color]);
  }
}
inline int selfTest() {
  if(PetAssets::Sleep.frames!=2 || PetAssets::Awake.frames!=2 || PetAssets::Run.frames!=7) return 1;
  for(int m=-1;m<=2;m++) {
    const PetAssets::Clip& clip=clipFor(Mode(m));
    int left=(WIDTH-clip.width*SCALE)/2,top=FLOOR_Y-clip.height*SCALE;
    if(left<1 || top<1 || left+clip.width*SCALE>=WIDTH || top+clip.height*SCALE>=HEIGHT) return 2;
    uint32_t cycle=0;
    for(int f=0;f<clip.frames;f++) {if(!clip.durations[f]) return 3;cycle+=clip.durations[f];}
    if(frameAt(clip,0)!=0 || frameAt(clip,clip.durations[0])!=1 || frameAt(clip,cycle)!=0) return 4;
    for(uint32_t p=0;p<uint32_t(clip.width)*clip.height*clip.frames;p++)
      if(clip.pixels[p]>=PetAssets::PALETTE_COUNT) return 5;
  }
  Animator animator;
  if(animator.tick(100,Calm).frame!=0 || animator.tick(800,Calm).frame!=1 || animator.tick(900,Play).frame!=0) return 6;
  return 0;
}
}
