from pathlib import Path
from PIL import Image
import json
import re
import unittest
import defusedxml.ElementTree as ET

root=Path(__file__).resolve().parents[1]
release=root/'arduino/assets/eevee'
source=root/'arduino/script'

class AssetTests(unittest.TestCase):
    def test_encoded_frames_match_downloaded_artwork(self):
        metadata=json.loads((release/'manifest.json').read_text())
        header=(source/'PetAssets.h').read_text()
        palette=[int(v,16) for v in re.findall(r'0x[0-9A-F]+',re.search(r'palette\[\].*?\{(.*?)\};',header,re.S)[1])]
        xml=ET.parse(release/'sources/AnimData.xml')
        for clip in metadata['clips']:
            name=clip['source_animation']
            node=next(n for n in xml.findall('.//Anim') if n.findtext('Name')==name)
            w,h=int(node.findtext('FrameWidth')),int(node.findtext('FrameHeight'))
            sheet=Image.open(release/'sources'/(name+'-Anim.png')).convert('RGBA')
            row=clip['direction_row']
            frames=[sheet.crop((f*w,row*h,(f+1)*w,(row+1)*h)) for f in range(clip['frames'])]
            boxes=[f.getbbox() for f in frames]
            union=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
            expected=[]
            for frame in frames:
                for r,g,b,a in frame.crop(union).getdata():expected.append(None if not a else ((r>>3)<<11)|((g>>2)<<5)|(b>>3))
            encoded=[int(n) for n in re.findall(r'\d+',re.search(clip['id']+r'Pixels\[\].*?\{(.*?)\};',header,re.S)[1])]
            self.assertEqual(len(encoded),len(expected))
            for index,color in zip(encoded,expected):self.assertEqual(None if index==0 else palette[index],color)

    def test_sprite_and_metrics_are_in_separate_rectangles(self):
        sketch=(source/'script.ino').read_text()
        header=(source/'PetAnimation.h').read_text()
        x,y,w,h=map(int,re.search(r'X=(\d+), Y=(\d+), WIDTH=(\d+), HEIGHT=(\d+)',header).groups())
        self.assertLessEqual(x+w,320);self.assertLessEqual(y+h,114)
        fields=[tuple(map(int,m)) for m in re.findall(r'\bfield\((\d+),(\d+),(\d+),(\d+),(\d+),',sketch)]
        self.assertEqual(len(fields),10)
        for index,fx,fy,fw,fh in fields:self.assertFalse(x<fx+fw and fx<x+w and y<fy+fh and fy<y+h,index)
        self.assertEqual(sketch.count('tft.fillScreen('),1)

    def test_previews_and_native_frames_fit_the_display(self):
        metadata=json.loads((release/'manifest.json').read_text())
        for clip in metadata['clips']:
            self.assertLess(clip['width']*metadata['scale'],98)
            self.assertLess(clip['height']*metadata['scale'],97)
            self.assertEqual(len(clip['durations_ms']),clip['frames'])
            self.assertGreater(min(clip['durations_ms']),16)
            gif=Image.open(release/'previews'/clip['preview'])
            self.assertEqual(gif.n_frames,clip['frames'])
            for i in range(gif.n_frames):
                gif.seek(i);box=gif.convert('RGB').getbbox()
                self.assertTrue(box and 0<box[0]<box[2]<98 and 0<box[1]<box[3]<108)
            gif.close()

if __name__=='__main__':unittest.main()
