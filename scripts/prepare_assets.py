"""Extract existing sprite frames and encode them for the display, without drawing new art."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
release=root/'arduino/assets/eevee'
assets=release/'sources'
xml=ET.parse(assets/'AnimData.xml')
palette=[0]
palette_lookup={}
clips=[]
for identifier,name,filename,speed in [('Sleep','EventSleep','vert-dort.gif',1.4),('Awake','Idle','jaune-reveille.gif',1.0),('Run','Walk','rouge-court.gif',0.8)]:
    node=next(n for n in xml.findall('.//Anim') if n.findtext('Name')==name)
    width,height=int(node.findtext('FrameWidth')),int(node.findtext('FrameHeight'))
    ticks=[int(n.text) for n in node.findall('Durations/Duration')]
    sheet=Image.open(assets/(name+'-Anim.png')).convert('RGBA')
    direction=7
    frames=[sheet.crop((i*width,direction*height,(i+1)*width,(direction+1)*height)) for i in range(len(ticks))]
    boxes=[f.getbbox() for f in frames]
    union=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
    frames=[f.crop(union) for f in frames]
    w,h=frames[0].size
    durations=[round(t*1000/60*speed) for t in ticks]
    encoded=[]
    previews=[]
    for frame in frames:
        for r,g,b,a in frame.getdata():
            if not a:encoded.append(0);continue
            color=((r>>3)<<11)|((g>>2)<<5)|(b>>3)
            if color not in palette_lookup:
                palette_lookup[color]=len(palette);palette.append(color)
            encoded.append(palette_lookup[color])
        canvas=Image.new('RGB',(98,108),'black')
        enlarged=frame.resize((w*3,h*3),Image.Resampling.NEAREST)
        canvas.paste(enlarged,((98-w*3)//2,97-h*3),enlarged)
        previews.append(canvas)
    previews[0].save(release/'previews'/filename,save_all=True,append_images=previews[1:],duration=durations,loop=0,disposal=2)
    clips.append({'id':identifier,'source_animation':name,'direction_row':direction,'width':w,'height':h,'frames':len(frames),'durations_ms':durations,'pixels':encoded,'preview':filename})
assert len(palette)<=256
lines=['// SPDX-License-Identifier: CC-BY-NC-4.0','#pragma once','#include <stdint.h>','// Existing CHUNSOFT artwork from PMDCollab/SpriteCollab; see ../assets/eevee/sources/credits.txt.','namespace PetAssets {']
lines+=['constexpr uint16_t PALETTE_COUNT='+str(len(palette))+';', 'const uint16_t palette[] PROGMEM={'+','.join('0x%04X'%v for v in palette)+'};']
for clip in clips:
    lines.append('const uint16_t '+clip['id']+'Durations[] PROGMEM={'+','.join(map(str,clip['durations_ms']))+'};')
    lines.append('const uint8_t '+clip['id']+'Pixels[] PROGMEM={')
    data=clip['pixels']
    for offset in range(0,len(data),60):lines.append(','.join(map(str,data[offset:offset+60]))+',')
    lines.append('};')
lines.append('struct Clip {const uint8_t* pixels;const uint16_t* durations;uint8_t width,height,frames;};')
for clip in clips:lines.append('const Clip '+clip['id']+'={'+clip['id']+'Pixels,'+clip['id']+'Durations,'+','.join(map(str,[clip['width'],clip['height'],clip['frames']]))+'};')
lines.append('}')
(root/'arduino/script/PetAssets.h').write_text('\n'.join(lines)+'\n',encoding='utf-8')
revision=json.loads((assets/'source-revision.json').read_text(encoding='utf-8-sig'))['Revision']
manifest={'repository':'https://github.com/PMDCollab/SpriteCollab','revision':revision,'artist_credit':(assets/'credits.txt').read_text().strip(),
          'palette_colors':len(palette),'scale':3,'clips':[{k:v for k,v in c.items() if k!='pixels'} for c in clips],
          'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in assets.iterdir() if p.is_file()}}
(release/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k not in ('sources','artist_credit')},indent=2))
