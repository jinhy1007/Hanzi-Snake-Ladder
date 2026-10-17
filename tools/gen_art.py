#!/usr/bin/env python3
"""识字蛇形棋 · 画图脚本

用画图 API 生成三张地图背景（短/中/长棋盘）和道具图片。
API key 从环境变量或项目根目录的 .env 文件读取，脚本不会打印或保存 key。

环境变量:
  IMAGE_PROVIDER      kie、openai 或 gemini（不设时：哪个 key 存在就用哪个）
  KIE_API_KEY         用 Kie.ai 时必填
  KIE_IMAGE_MODEL     默认 nano-banana-pro（透明角标再用 recraft/remove-background 抠图）
  KIE_RESOLUTION      1K/2K/4K，默认 2K
  OPENAI_API_KEY      用 OpenAI 时必填
  GEMINI_API_KEY      用 Gemini 时必填（也接受 GOOGLE_API_KEY）
  OPENAI_IMAGE_MODEL  默认 gpt-image-1
  GEMINI_IMAGE_MODEL  默认 gemini-2.5-flash-image
  IMAGE_QUALITY       OpenAI 画质 low/medium/high，默认 high

用法（在项目根目录）:
  .venv/bin/python tools/gen_art.py guides            # 只画道路草图，不调用 API
  .venv/bin/python tools/gen_art.py maps [short mid long]
  .venv/bin/python tools/gen_art.py props [coach mush dragon unicorn door-closed door-open]
  .venv/bin/python tools/gen_art.py all
  API 返回的原图缓存在 art-src/raw/，再次运行不会重复花钱；加 --force 才会重新画。
"""
import base64, io, json, math, os, sys, time, uuid, urllib.request, urllib.error
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'art-src', 'raw')
GUIDES = os.path.join(ROOT, 'art-src', 'guides')
OUT_MAPS = os.path.join(ROOT, 'images', 'maps')
OUT_PROPS = os.path.join(ROOT, 'images', 'props')

def load_env_file():
    """读取项目根目录的 .env（KEY=VALUE 每行一个），已有的环境变量优先。.env 已在 .gitignore 里，不会上传。"""
    path = os.path.join(ROOT, '.env')
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                k = k.strip().removeprefix('export ').strip()
                os.environ.setdefault(k, v.strip().strip('"').strip("'"))


load_env_file()

# ---------- 道路几何：和 js/game.js 里的 roadPt / mapGeo 保持一致 ----------
MW, R, CXL, CXR, SP = 400, 76, 106, 294, 78
LR = CXR - CXL; PER = LR + math.pi * R; ROW = 2 * R
CASTLE_W = 230; CASTLE_H = round(CASTLE_W * 285 / 275); CASTLE_BASE = CASTLE_H + 22
MAPS = {'short': 28, 'mid': 36, 'long': 44}   # 每张地图按这个格子数设计道路长度
W = 1024; S = W / MW                            # 像素 / 地图单位
WIN_H = 1536; STEP = 1024                       # 分段生成：每段 2:3，重叠 512px
BLEND = 110                                     # 接缝渐变带高度（像素）


def road_pt(s):
    k = math.floor(s / PER); q = s - k * PER; y0 = -k * ROW; right = k % 2 == 0
    if q < LR:
        return (CXL + q if right else CXR - q, y0)
    th = (q - LR) / R; cy = y0 - R
    return ((CXR + R * math.sin(th)) if right else (CXL - R * math.sin(th)), cy + R * math.cos(th))


def map_geo(n):
    send = (n - 1) * SP
    raw = [road_pt(s) for s in range(0, int(send), 6)] + [road_pt(send)]
    min_y = min(p[1] for p in raw)
    off_y = CASTLE_BASE + 72 - min_y
    H = round(off_y + 162)
    road = [(x, y + off_y) for x, y in raw]
    end = road[-1]; gate = (200, CASTLE_BASE - 10); cy = min(end[1] - 30, gate[1] + 40)
    conn = []
    for i in range(21):
        t = i / 20
        conn.append(((1-t)**2*end[0] + 2*(1-t)*t*end[0] + t*t*gate[0], (1-t)**2*end[1] + 2*(1-t)*t*cy + t*t*gate[1]))
    runs = int(send // PER) + 1  # 横向路段数（含最后一段不完整的）
    return dict(n=n, H=H, off_y=off_y, road=road, conn=conn, runs=runs, send=send)


def run_y(g, k):
    return g['off_y'] - k * ROW


def features(g):
    """每张地图上的景物位置（地图单位），草图和提示词共用。"""
    runs = g['runs']; mid = max(1, runs // 2); cot = max(mid + 1, runs - 3)
    gap = lambda k: run_y(g, k) - ROW / 2           # 第 k 段和第 k+1 段路之间的空地中线
    open_left = lambda k: k % 2 == 0                # 第 k 段之后的弯道在右边，左边是空地
    lake_y = gap(mid)
    stream_x = 250 if open_left(mid) else 150
    cot_x = 46 if open_left(cot) else MW - 46
    return dict(
        lake=(200 - 92, lake_y - 26, 200 + 92, lake_y + 26),
        stream=[(stream_x, lake_y + 20), (stream_x + 14, run_y(g, mid) - 40), (stream_x - 6, run_y(g, mid) + 40),
                (stream_x + 10, gap(mid - 1)), (0 if open_left(mid - 1) else MW, gap(mid - 1) + 10)],
        bridge=(stream_x - 24, run_y(g, mid) - 44, stream_x + 24, run_y(g, mid) + 44),
        cottage=(cot_x - 40, gap(cot) - 44, cot_x + 40, gap(cot) + 30),
        forest_top=gap(0),
        castle=(200 - CASTLE_W / 2, CASTLE_BASE - CASTLE_H, 200 + CASTLE_W / 2, CASTLE_BASE),
    )


# ---------- 草图 ----------
def P(pt):
    return (pt[0] * S, pt[1] * S)


def draw_guide(name):
    g = map_geo(MAPS[name]); f = features(g); H = g['H']; Hpx = round(H * S)
    im = Image.new('RGB', (W, Hpx), (168, 214, 130))
    d = ImageDraw.Draw(im)
    sky_end = CASTLE_BASE + 40
    for y in range(round(sky_end * S)):  # 天空：薰衣草紫到粉色
        t = y / (sky_end * S)
        d.line([(0, y), (W, y)], fill=(int(214 + 34 * t), int(200 + 20 * t), int(240 - 20 * t)))
    fy = f['forest_top'] * S                         # 森林：底部深绿
    d.rectangle([0, fy, W, Hpx], fill=(58, 112, 70))
    for i in range(26):
        x = (i * 97) % W; y = fy + ((i * 211) % max(1, int(Hpx - fy)))
        d.ellipse([x - 70, y - 90, x + 70, y + 50], fill=(38, 88, 54))
    d.ellipse([P(f['lake'][:2]), P(f['lake'][2:])], fill=(96, 170, 226))
    d.line([P(p) for p in f['stream']], fill=(96, 170, 226), width=round(16 * S), joint='curve')
    x0, y0, x1, y1 = f['castle']                     # 城堡轮廓
    d.rectangle([P((x0 + 30, y0 + 90)), P((x1 - 30, y1))], fill=(250, 226, 236))
    for cx, top in ((x0 + 34, y0 + 40), (200, y0), (x1 - 34, y0 + 40)):
        d.rectangle([P((cx - 22, top + 40)), P((cx + 22, y1))], fill=(250, 232, 240))
        d.polygon([P((cx - 28, top + 44)), P((cx, top)), P((cx + 28, top + 44))], fill=(170, 120, 210))
    x0, y0, x1, y1 = f['cottage']                    # 小木屋
    d.rectangle([P((x0 + 8, y0 + 34)), P((x1 - 8, y1))], fill=(140, 92, 60))
    d.polygon([P((x0, y0 + 38)), P(((x0 + x1) / 2, y0)), P((x1, y0 + 38))], fill=(92, 60, 48))
    road_w = round(72 * S)                           # 道路：精确位置
    for pts, w in ((g['road'], road_w), (g['conn'], round(50 * S))):
        d.line([P(p) for p in pts], fill=(236, 212, 160), width=w, joint='curve')
        for p in (pts[0], pts[-1]):
            x, y = P(p); d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=(236, 212, 160))
    d.rectangle([P(f['bridge'][:2]), P(f['bridge'][2:])], fill=(170, 116, 70))  # 小桥
    return im, g, f


# ---------- 提示词 ----------
STYLE = ('Classic Disney-style fairy-tale picture-book illustration, soft painterly gouache and watercolor, '
         'warm gentle light, rounded friendly shapes, pastel but rich colors, cute and cozy, suitable for a 6-year-old. '
         'Absolutely no text, letters, numbers, signs or logos.')


def map_prompt(g, f, top_u, bot_u, first):
    parts = []
    if bot_u > f['forest_top']:
        parts.append('at the bottom, a lush enchanted forest with big friendly trees, ferns and glowing mushrooms where the path begins')
    if top_u < f['lake'][3] + 160 and bot_u > f['lake'][1] - 160:
        parts.append('a sparkling little lake with lily pads and a babbling stream that flows under a small wooden footbridge on the path')
    if top_u < f['cottage'][3] + 120 and bot_u > f['cottage'][1] - 120:
        parts.append('a mysterious little storybook cottage with a round door and glowing windows, half hidden among trees')
    if top_u < 1:
        parts.append('at the top, a beautiful pink and white fairy-tale princess castle with tall spires against a dreamy pastel sky, '
                     'with rose gardens in front of it; the path ends at the castle gate')
    parts.append('open green meadows with wildflowers, and cute woodland animals peeking from the sides of the path '
                 '(bunnies, a fawn, squirrels, hedgehogs, songbirds, butterflies)')
    if top_u >= 1:
        parts.append('there is NO castle and NO sky or horizon in this section — the ground fills the whole frame '
                     'edge to edge, because the map continues above the top edge')
    road = ('The attached image is a rough color-block layout sketch, seen from a gentle top-down storybook map view. '
            'The beige band is a winding dirt path: paint it as a smooth, clear, light sandy path in EXACTLY the same '
            'position, width and curves as the sketch. Keep the path completely empty — no animals, plants, objects or '
            'shadows on top of it, because game pieces will be placed on it. Every part of the beige path must appear, including '
            'any path segment at the very bottom edge even where it runs through the forest. Follow the sketch for where the forest, water, '
            'cottage and castle go. ')
    cont = '' if first else ('The lower part of the image is already finished painting — keep it exactly as it is and '
                             'continue the same scene seamlessly upward with the same style, colors and lighting. ')
    return road + cont + 'This section of the map shows: ' + '; '.join(parts) + '. ' + STYLE


PROPS = {
    'coach': dict(kind='card', prompt='A magical Cinderella-style pumpkin coach with swirly golden wheels and sparkles, three-quarter view, '
                  'centered, on a soft warm peach-orange background with tiny stars.'),
    'mush': dict(kind='card', prompt='A cute but clearly poisonous toadstool mushroom: purple cap with bright spots, a sleepy grumpy little face, '
                 'a few drowsy "zzz"-shaped swirls of mist (no letters), centered, on a soft lilac background.'),
    'dragon': dict(kind='card', prompt='A cute, slightly mischievous little green-and-red dragon breathing a big bright stream of orange-yellow fire, '
                   'big eyes, tiny wings, playful not scary, centered, on a soft rosy background.'),
    'unicorn': dict(kind='badge', prompt='A small happy white unicorn with a pastel rainbow mane and tail and a golden horn, '
                    'prancing, full body, side view facing right, with a few sparkles.'),
    'door-closed': dict(kind='badge', prompt='A magical fairy-tale arched wooden door in a little stone frame, CLOSED, with a round golden '
                        'handle, climbing flowers and a glowing purple keyhole, a few sparkles, full object visible, front view.'),
    'door-open': dict(kind='badge', ref='door-closed', prompt='The same magical arched wooden door as in the reference image, same frame, '
                      'flowers and colors, but now swung WIDE OPEN (the door turned fully aside so the whole doorway is a bright glowing opening) with warm golden magical light and sparkles pouring out, '
                      'full object visible, front view.'),
}
CARD_TAIL = (' Square storybook card illustration filling the whole frame edge to edge, the subject drawn LARGE, filling most of the upper '
             'three quarters of the frame; the bottom quarter a calm plain area of the background color. No border, no frame. ')
BADGE_TAIL = (' A single isolated object sticker with clean edges and no ground shadow, nothing else in the picture. ')


# ---------- API ----------
def provider():
    p = os.environ.get('IMAGE_PROVIDER', '').strip().lower()
    if not p:
        p = 'kie' if os.environ.get('KIE_API_KEY') else 'openai' if os.environ.get('OPENAI_API_KEY') else 'gemini' if (os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')) else ''
    if p not in ('kie', 'openai', 'gemini'):
        sys.exit('请设置 IMAGE_PROVIDER=kie / openai / gemini，以及对应的 API key 环境变量。')
    return p


def png_bytes(im):
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()


def http(req, label):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'replace')[:800]
            if e.code in (429, 500, 502, 503) and attempt < 2:
                print(f'  {label}: HTTP {e.code}，{20 * (attempt + 1)} 秒后重试'); time.sleep(20 * (attempt + 1)); continue
            sys.exit(f'{label}: HTTP {e.code}\n{body}')
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(10); continue
            sys.exit(f'{label}: 网络错误 {e}')


def multipart(fields, files):
    bd = uuid.uuid4().hex; out = io.BytesIO()
    for k, v in fields.items():
        out.write(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, fname, data in files:
        out.write(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"; filename="{fname}"\r\nContent-Type: image/png\r\n\r\n'.encode())
        out.write(data); out.write(b'\r\n')
    out.write(f'--{bd}--\r\n'.encode())
    return out.getvalue(), f'multipart/form-data; boundary={bd}'


def openai_image(prompt, size, images=(), mask=None, transparent=False, label=''):
    key = os.environ.get('OPENAI_API_KEY') or sys.exit('缺少环境变量 OPENAI_API_KEY')
    model = os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-1')
    common = dict(model=model, prompt=prompt, size=size, quality=os.environ.get('IMAGE_QUALITY', 'high'),
                  background='transparent' if transparent else 'opaque', output_format='png', n='1')
    if images:
        fields = dict(common); fields['input_fidelity'] = 'high'
        files = [('image[]', f'in{i}.png', png_bytes(im)) for i, im in enumerate(images)]
        if mask is not None:
            files.append(('mask', 'mask.png', png_bytes(mask)))
        body, ctype = multipart(fields, files)
        req = urllib.request.Request('https://api.openai.com/v1/images/edits', data=body, method='POST',
                                     headers={'Authorization': f'Bearer {key}', 'Content-Type': ctype})
    else:
        common['n'] = 1
        req = urllib.request.Request('https://api.openai.com/v1/images/generations', data=json.dumps(common).encode(), method='POST',
                                     headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    res = http(req, label)
    return Image.open(io.BytesIO(base64.b64decode(res['data'][0]['b64_json']))).convert('RGBA')


def gemini_image(prompt, aspect, images=(), label=''):
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY') or sys.exit('缺少环境变量 GEMINI_API_KEY')
    model = os.environ.get('GEMINI_IMAGE_MODEL', 'gemini-2.5-flash-image')
    parts = [{'text': prompt}] + [{'inline_data': {'mime_type': 'image/png', 'data': base64.b64encode(png_bytes(im)).decode()}} for im in images]
    body = {'contents': [{'parts': parts}],
            'generationConfig': {'responseModalities': ['IMAGE'], 'imageConfig': {'aspectRatio': aspect}}}
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                 data=json.dumps(body).encode(), method='POST',
                                 headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
    res = http(req, label)
    for c in res.get('candidates', []):
        for p in c.get('content', {}).get('parts', []):
            d = p.get('inlineData') or p.get('inline_data')
            if d:
                return Image.open(io.BytesIO(base64.b64decode(d['data']))).convert('RGBA')
    sys.exit(f'{label}: Gemini 没有返回图片：{json.dumps(res)[:600]}')


KIE = 'https://api.kie.ai'
KIE_UPLOAD = 'https://kieai.redpandaai.co'  # 上传文件用另一个域名


def kie_call(path, body=None, label='', base=KIE):
    key = os.environ.get('KIE_API_KEY') or sys.exit('缺少环境变量 KIE_API_KEY')
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 method='POST' if body is not None else 'GET',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    for attempt in range(4):
        res = http(req, label)
        if res.get('code') == 200:
            return res.get('data') or {}
        if res.get('code') in (429, 500, 502, 503) and attempt < 3:  # Kie.ai 出错时 HTTP 也是 200，要看 code
            print(f"  {label}: code {res.get('code')}，{15 * (attempt + 1)} 秒后重试"); time.sleep(15 * (attempt + 1)); continue
        sys.exit(f"{label}: Kie.ai 返回 code {res.get('code')}：{res.get('msg')}")


def kie_upload(im, label):
    b64 = base64.b64encode(png_bytes(im)).decode()
    body = {'base64Data': b64, 'uploadPath': 'shizi-shexingqi', 'fileName': f'{label}-{uuid.uuid4().hex[:8]}.png'}
    return kie_call('/api/file-base64-upload', body, label, base=KIE_UPLOAD)['downloadUrl']


def kie_task(model, inp, label):
    task = kie_call('/api/v1/jobs/createTask', {'model': model, 'input': inp}, label)['taskId']
    wait, t0 = 3, time.time()
    while True:
        time.sleep(wait); wait = min(wait + 2, 15)
        d = kie_call(f'/api/v1/jobs/recordInfo?taskId={task}', None, label)
        st = d.get('state')
        if st == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]
            with urllib.request.urlopen(url, timeout=300) as r:
                return Image.open(io.BytesIO(r.read())).convert('RGBA')
        if st == 'fail':
            sys.exit(f"{label}: 任务失败 {d.get('failCode')} {d.get('failMsg')}")
        if time.time() - t0 > 900:
            sys.exit(f'{label}: 等了 15 分钟还没画完（taskId {task}）')


def kie_image(prompt, aspect, images=(), label=''):
    urls = [kie_upload(im, f'{label}-in{i}') for i, im in enumerate(images)]
    return kie_task(os.environ.get('KIE_IMAGE_MODEL', 'nano-banana-pro'),
                    {'prompt': prompt, 'image_input': urls, 'aspect_ratio': aspect,
                     'resolution': os.environ.get('KIE_RESOLUTION', '2K'), 'output_format': 'png'}, label)


def kie_remove_bg(im, label):
    return kie_task('recraft/remove-background', {'image': kie_upload(im, f'{label}-cut')}, f'{label}-cut')


def paint_road(canvas, g):
    """AI 画的路位置不够准：最后按游戏里的精确路线再画一条手绘感的沙土小路盖上去，保证格子正好压在路上。"""
    import random
    Hpx = canvas.height
    def stroke(pts, w, color, blur):
        layer = Image.new('L', (W, Hpx), 0); d = ImageDraw.Draw(layer)
        d.line([P(p) for p in pts], fill=255, width=round(w * S), joint='curve')
        for p in (pts[0], pts[-1]):
            x, y = P(p); r = w * S / 2; d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, Hpx), color).split(), layer)))
    for pts, w in ((g['road'], 72), (g['conn'], 50)):
        stroke(pts, w + 10, (170, 150, 104), 12)   # 很淡、很软的路边，像融进草地
        stroke(pts, w, (236, 214, 176), 5)          # 沙土路面
        stroke(pts, w - 22, (245, 230, 200), 12)    # 中间亮一点
    # 路面上的小石子和纹理（只在路上）
    mask = Image.new('L', (W, Hpx), 0); md = ImageDraw.Draw(mask)
    md.line([P(p) for p in g['road']], fill=255, width=round(60 * S), joint='curve')
    tex = Image.new('RGBA', (W, Hpx), (0, 0, 0, 0)); td = ImageDraw.Draw(tex); rnd = random.Random(g['n'])
    for _ in range(int(Hpx * 1.2)):
        x, y = rnd.uniform(0, W), rnd.uniform(0, Hpx); r = rnd.uniform(1.5, 4.5)
        c = rnd.choice([(196, 160, 106, 150), (250, 236, 204, 170), (176, 140, 92, 120)])
        td.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=c)
    tex.putalpha(Image.composite(tex.getchannel('A'), Image.new('L', (W, Hpx), 0), mask))
    canvas.alpha_composite(tex)
    return canvas


EXTRA_SEAMS = {'mid': [1720]}   # 段内 AI 自己画出的横线（像素行），和自动算出的拼接处一起修
EXTRA_FILL = {'mid': [1430]}    # 画得太空的草地（像素行），请 AI 补上花草小动物
TOUCH_PROMPT = {
    'seam': ('This is one section of a storybook map. Across the middle of the image there is a visible horizontal seam where two '
             'paintings were joined. Repaint the scenery so it flows continuously across that line with no visible seam, '
             'keeping everything else the same. '),
    'fill': ('The plain flat green lawn in the middle of this image is too empty. Paint it as a lush storybook meadow with '
             'wildflowers, small bushes, mushrooms and one or two cute woodland animals, matching the rest of the picture. '),
    'top': ('Make the winding sandy path continue naturally from where it ends up to the castle front gate, as a slightly '
            'narrower garden path that clearly reaches the gate. The castle must stay fully visible and unchanged, with nothing '
            'covering it. Blend the edges of the sandy path softly into the grass and flowers, as part of the painting. '),
    'bottom': ('Make the start of the sandy path look natural: the path should emerge from among the forest trees at the bottom, '
               'its beginning fading softly into the forest floor instead of ending abruptly. Blend the edges of the sandy path '
               'softly into the grass, as part of the painting. '),
}
TOUCH_TAIL = ('Keep the sandy path in exactly the same position, shape and width, and keep it empty. Same style: ' + STYLE)


def touch_up(canvas, name, g, f, prov, force):
    """拼好的地图再请 AI 局部重画几处：拼接缝、起点、终点。贴回时把放格子的那段路保护起来，格子位置不会变。"""
    Hpx = canvas.height
    tops = []; t = Hpx - WIN_H
    while t > 0:
        tops.append(t); t -= STEP
    tops.append(0)
    rows = sorted([b + STEP for b in tops[1:]] + EXTRA_SEAMS.get(name, []))  # 每段新画的部分和旧段的接缝
    seams = []
    for r in rows:  # 太近的缝合并成一处
        if seams and r - seams[-1] < 300:
            continue
        seams.append(r)
    start_y = round(g['road'][0][1] * S); end_y = round(g['road'][-1][1] * S)
    jobs = [('seam', r, max(0, min(Hpx - WIN_H, r - WIN_H // 2)), r - 220, r + 220) for r in seams]
    jobs += [('fill', r, max(0, min(Hpx - WIN_H, r - WIN_H // 2)), r - 160, r + 160) for r in EXTRA_FILL.get(name, [])]
    jobs.append(('bottom', start_y, Hpx - WIN_H, start_y - round(60 * S), Hpx))
    jobs.append(('top', end_y, 0, 0, end_y + round(50 * S)))
    # 受保护的路：从第一个格子到最后一个格子，平头，不含两头的圆帽
    guard = Image.new('L', (W, Hpx), 0)
    ImageDraw.Draw(guard).line([P(p) for p in g['road']], fill=255, width=round(74 * S))
    guard = guard.filter(ImageFilter.GaussianBlur(3))
    for kind, row, top, y0, y1 in jobs:
        key = f'touch-{name}-{kind}-{row}'
        cache = os.path.join(RAW, key + '.png')
        win = canvas.crop((0, top, W, top + WIN_H))
        if os.path.exists(cache) and not force:
            new = Image.open(cache).convert('RGBA')
        else:
            print(f'  修 {name} {kind}（第 {row} 行）…')
            prompt = TOUCH_PROMPT[kind] + TOUCH_TAIL
            if prov == 'kie':
                new = kie_image(prompt, '2:3', images=[win], label=key)
            elif prov == 'openai':
                new = openai_image(prompt, f'{W}x{WIN_H}', images=[win], label=key)
            else:
                new = gemini_image(prompt, '2:3', images=[win], label=key)
            new = new.convert('RGBA').resize((W, WIN_H), Image.LANCZOS); new.save(cache)
        m = Image.new('L', (W, WIN_H), 0)
        ImageDraw.Draw(m).rectangle([0, max(0, y0 - top), W, min(WIN_H, y1 - top)], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(40))
        m = ImageChops.subtract(m, guard.crop((0, top, W, top + WIN_H)))
        canvas.paste(Image.composite(new, win, m), (0, top))
    return canvas


# ---------- 地图 ----------
def gen_map(name, force):
    out = os.path.join(OUT_MAPS, f'map-{name}.webp')
    prov = provider()
    guide, g, f = draw_guide(name); Hpx = guide.height
    tops = []
    t = Hpx - WIN_H
    while t > 0:
        tops.append(t); t -= STEP
    tops.append(0)
    canvas = Image.new('RGBA', (W, Hpx)); done_top = Hpx
    for i, top in enumerate(tops):
        cache = os.path.join(RAW, f'map-{name}-{i}.png')
        overlap = min(top + WIN_H - done_top, WIN_H - STEP) if i else 0  # 最多沿用旧段 512px
        win = guide.crop((0, top, W, top + WIN_H)).convert('RGBA')
        if overlap:
            win.paste(canvas.crop((0, top + WIN_H - overlap, W, top + WIN_H)), (0, WIN_H - overlap))
        if os.path.exists(cache) and not force:
            seg = Image.open(cache).convert('RGBA')
        else:
            prompt = map_prompt(g, f, top / S, (top + WIN_H) / S, i == 0)
            print(f'  画 {name} 第 {i + 1}/{len(tops)} 段 …')
            if prov == 'openai':
                mask = None
                if overlap:
                    mask = Image.new('RGBA', (W, WIN_H), (0, 0, 0, 0))
                    ImageDraw.Draw(mask).rectangle([0, WIN_H - overlap, W, WIN_H], fill=(0, 0, 0, 255))
                seg = openai_image(prompt, f'{W}x{WIN_H}', images=[win], mask=mask, label=f'map-{name}-{i}')
            elif prov == 'kie':
                seg = kie_image(prompt, '2:3', images=[win], label=f'map-{name}-{i}')
            else:
                seg = gemini_image(prompt, '2:3', images=[win], label=f'map-{name}-{i}')
            seg = seg.resize((W, WIN_H), Image.LANCZOS)
            seg.save(cache)
        if overlap:  # 重叠区保留旧段，只在重叠区最上面一条窄带里渐变，避免整片重影
            band = min(BLEND, overlap)
            old = canvas.crop((0, top + WIN_H - overlap, W, top + WIN_H))
            new_b = seg.crop((0, WIN_H - overlap, W, WIN_H - overlap + band))
            seg.paste(old, (0, WIN_H - overlap))
            ramp = Image.linear_gradient('L').resize((W, band)).point(lambda v: 255 - v)
            seg.paste(Image.composite(new_b, old.crop((0, 0, W, band)), ramp), (0, WIN_H - overlap))
        canvas.paste(seg, (0, top)); done_top = top
    if name == 'short':  # 进度条两头和获胜卡片用的小图：直接从地图上裁
        x0, y0, x1, y1 = f['castle']
        canvas.crop(tuple(round(v * S) for v in (x0, max(0, y0 - 10), x1, y1 + 10))).convert('RGB').save(
            os.path.join(OUT_PROPS, 'castle.webp'), 'WEBP', quality=86)
        canvas.crop((0, Hpx - round(130 * S), round(170 * S), Hpx)).convert('RGB').save(
            os.path.join(OUT_PROPS, 'forest.webp'), 'WEBP', quality=86)
    canvas = paint_road(canvas, g)
    canvas = touch_up(canvas, name, g, f, prov, force)
    os.makedirs(OUT_MAPS, exist_ok=True)
    canvas.convert('RGB').save(out, 'WEBP', quality=80, method=6)
    print(f'完成 {out}（{W}x{Hpx}）')



# ---------- 道具 ----------
def chroma_key(im):
    """Gemini 不能直接出透明背景：让它画在纯绿底上，再抠掉绿色。"""
    im = im.convert('RGBA'); px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            gness = g - max(r, b)
            if gness > 60:
                px[x, y] = (r, g, b, 0)
            elif gness > 20:
                px[x, y] = (r, max(r, b), b, int(255 * (60 - gness) / 40))
    alpha = im.getchannel('A').filter(ImageFilter.MinFilter(3))
    im.putalpha(alpha); return im


def gen_prop(name, force):
    spec = PROPS[name]
    out = os.path.join(OUT_PROPS, f'{name}.webp')
    prov = provider(); cache = os.path.join(RAW, f'prop-{name}.png'); badge = spec['kind'] == 'badge'
    if os.path.exists(cache) and not force:
        im = Image.open(cache).convert('RGBA')
    else:
        print(f'  画 {name} …')
        prompt = spec['prompt'] + (BADGE_TAIL if badge else CARD_TAIL) + STYLE
        refs = []
        if spec.get('ref'):
            ref = os.path.join(RAW, f"prop-{spec['ref']}.png")
            if not os.path.exists(ref):
                gen_prop(spec['ref'], False)
            refs = [Image.open(ref).convert('RGBA')]
        if prov == 'openai':
            im = openai_image(prompt + (' Transparent background.' if badge else ''), '1024x1024', images=refs,
                              transparent=badge, label=name)
        elif prov == 'kie':
            if badge:
                prompt += ' Place it on a plain flat white background.'
            pre = os.path.join(RAW, f'prop-{name}-uncut.png')  # 抠图前的原图也缓存，抠图失败重跑不用重画
            if os.path.exists(pre) and not force:
                im = Image.open(pre).convert('RGBA')
            else:
                im = kie_image(prompt, '1:1', images=refs, label=name); im.save(pre)
            if badge:
                im = kie_remove_bg(im, name)
        else:
            if badge:
                prompt += ' Place it on a perfectly flat, solid pure green (#00FF00) background with no gradients, so it can be cut out.'
                refs = [r.convert('RGB') for r in refs]
            im = gemini_image(prompt, '1:1', images=refs, label=name)
            if badge:
                im = chroma_key(im)
        im.save(cache)
    if badge:
        box = im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box:
            im = im.crop(box)
        im.thumbnail((512, 512), Image.LANCZOS)
        im.save(out, 'WEBP', quality=88, method=6)
    else:
        im.convert('RGB').resize((512, 512), Image.LANCZOS).save(out, 'WEBP', quality=84, method=6)
    print(f'完成 {out}')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; force = '--force' in sys.argv
    if not args:
        sys.exit(__doc__)
    os.makedirs(RAW, exist_ok=True); os.makedirs(OUT_PROPS, exist_ok=True); os.makedirs(OUT_MAPS, exist_ok=True)
    cmd, names = args[0], args[1:]
    if cmd == 'guides':
        os.makedirs(GUIDES, exist_ok=True)
        for k in names or MAPS:
            im, g, _ = draw_guide(k); p = os.path.join(GUIDES, f'guide-{k}.png'); im.save(p)
            print(f'{p}  {g["n"]} 格  {im.width}x{im.height}')
    elif cmd == 'maps':
        for k in names or MAPS: gen_map(k, force)
    elif cmd == 'props':
        for k in names or PROPS: gen_prop(k, force)
    elif cmd == 'all':
        for k in PROPS: gen_prop(k, force)
        for k in MAPS: gen_map(k, force)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
