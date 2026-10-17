"""把地图缩小，并在旁边画上格子位置，方便检查（不调用 API）。用法: preview_map.py short 输出.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import gen_art as G
name, out = sys.argv[1], sys.argv[2]
m = Image.open(f'images/maps/map-{name}.webp').convert('RGB'); n = G.MAPS[name]; g = G.map_geo(n)
ov = m.copy(); d = ImageDraw.Draw(ov)
for i in range(n):
    x, y = G.road_pt(i * G.SP); y += g['off_y']; r = 29 * G.S
    d.rectangle([x * G.S - r, y * G.S - r, x * G.S + r, y * G.S + r], fill=(255, 253, 245), outline=(120, 100, 80), width=3)
sc = 0.3; a = m.resize((int(m.width * sc), int(m.height * sc))); b = ov.resize(a.size)
o = Image.new('RGB', (a.width * 2 + 10, a.height), 'white'); o.paste(a, (0, 0)); o.paste(b, (a.width + 10, 0)); o.save(out)
