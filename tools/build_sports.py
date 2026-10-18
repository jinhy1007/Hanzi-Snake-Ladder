# -*- coding: utf-8 -*-
"""把三张选定的运动会样图拼成长棋盘地图（44 格那条路）。不再另外画跑道盖上去：
按颜色找出 AI 画的跑道，沿着游戏的路线描出跑道中线，游戏按这条中线摆格子，所以格子都在画出来的跑道上，街景也不会被挡住。

三张样图本身就是按长棋盘真实路线分段画的：终点 = 第 0–1536 行，中段 = 第 1391–2927 行，起点 = 第 2783–4319 行。
接缝放在重叠区里、同时被横向跑道盖住的位置，所以看不见。

运行：.venv/bin/python tools/build_sports.py            → art-src/preview/map-long-sports.webp（预览，不改游戏）
      .venv/bin/python tools/build_sports.py --install  → images/maps/map-long-sports.webp
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import gen_art as G

SAMPLES = os.path.join(G.ROOT, 'art-src', 'samples')
PARTS = [('sports-finish-v5.png', 0), ('sports-middle.png', 1391), ('sports-start-v6.png', 2783)]  # (图, 顶部所在行)
CUTS = [1521, 2805]      # 接缝行：都在重叠区里，而且两张图在这一行都正好是跑道，接上以后跑道是连着的
BAND = 30                # 接缝渐变带
TRACK = (235, 130, 100)  # 从样图里取的跑道颜色
FINISH = (370, 300)      # 终点拱门下方方格终点线的中点（像素）
CROPS = {                # 从地图上裁的小图（像素框）：进度条两头、获胜卡片
    'start': (180, 3800, 520, 4060),
    'finish': (150, 20, 500, 360),
    'podium': (700, 300, 1024, 620),
}
START_TRIM = 80          # 第一格往前挪一点（地图单位），不挡住拿旗的长颈鹿裁判
END_TRIM = 75            # 最后一格往回退一点，不挡住终点线
EDGE = (196, 98, 72)
LANE = (255, 244, 236)


def composite(Hpx):
    canvas = Image.new('RGB', (G.W, Hpx))
    imgs = [(Image.open(os.path.join(SAMPLES, f)).convert('RGB').resize((G.W, G.WIN_H)), top) for f, top in PARTS]
    canvas.paste(imgs[0][0], (0, imgs[0][1]))
    for (im, top), cut in zip(imgs[1:], CUTS):
        # 接缝以下用下面这张；接缝处 BAND 行内渐变
        lower = im.crop((0, cut - top - BAND // 2, G.W, G.WIN_H))
        upper = canvas.crop((0, cut - BAND // 2, G.W, cut + BAND // 2))
        ramp = Image.linear_gradient('L').resize((G.W, BAND))
        blend = Image.composite(lower.crop((0, 0, G.W, BAND)), upper, ramp)
        canvas.paste(lower, (0, cut - BAND // 2)); canvas.paste(blend, (0, cut - BAND // 2))
    return canvas


def paint_track(canvas, g):
    """按游戏里的精确路线画跑道：柔和的深色边、跑道面、三条白色分道线。只画放格子的这一段（两头圆角盖在起点、终点格子下面）。"""
    Hpx = canvas.height; canvas = canvas.convert('RGBA'); pts = [G.P(p) for p in g['road']]

    def stroke(w, color, blur):
        m = Image.new('L', (G.W, Hpx), 0); d = ImageDraw.Draw(m)
        d.line(pts, fill=255, width=round(w * G.S), joint='curve')
        for x, y in (pts[0], pts[-1]):
            r = w * G.S / 2; d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        if blur:
            m = m.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (G.W, Hpx), color).split(), m)))

    stroke(78, EDGE, 6)
    stroke(72, TRACK, 2)
    for w in (56, 38, 20):            # 每条白线：先画白色宽带，再用跑道色盖住里面，留下两侧细线
        stroke(w, LANE, 0); stroke(w - 1.6, TRACK, 0)
    return canvas


JOIN_FIX = [2805]        # 需要请 AI 修的接缝（第一处两边跑道刚好对上，直接拼就行）
JOIN_PROMPT = ('This picture has a visible horizontal seam across the middle of it, where two paintings were joined: the running '
               'track lane lines and some buildings do not line up there. Repaint only that middle strip so everything connects '
               'smoothly and naturally — the track and its white lane lines continue without any step, buildings and objects are whole. '
               'Keep everything else exactly the same: same 3D miniature-diorama style, same track position, same characters. '
               'No text, letters or numbers.')


def fix_joins(canvas):
    """接缝附近请 AI 重画一条窄带，只把那条带贴回去。"""
    for cut in JOIN_FIX:
        top = max(0, min(canvas.height - G.WIN_H, cut - G.WIN_H // 2))
        cache = os.path.join(G.RAW, f'sports-join-{cut}.png')
        win = canvas.crop((0, top, G.W, top + G.WIN_H))
        if os.path.exists(cache):
            new = Image.open(cache).convert('RGB')
        else:
            print(f'  修接缝（第 {cut} 行）…')
            new = G.kie_image(JOIN_PROMPT, '2:3', images=[win], label=f'sports-join-{cut}').convert('RGB').resize((G.W, G.WIN_H), Image.LANCZOS)
            new.save(cache)
        m = Image.new('L', (G.W, G.WIN_H), 0)
        ImageDraw.Draw(m).rectangle([0, cut - top - 120, G.W, cut - top + 120], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(30))
        canvas.paste(Image.composite(new, win, m), (0, top))
    return canvas


def skeleton_path(mask, start_px, scale=4):
    """把跑道区域细化成一条中线，从起点附近沿中线走到最远（最上面）的一端。返回原图像素坐标的折线。"""
    from collections import deque
    small = mask.resize((mask.width // scale, mask.height // scale), Image.BILINEAR).point(lambda v: 255 if v > 127 else 0)
    w, h = small.size; px = small.load()
    grid = [[1 if px[x, y] else 0 for x in range(w)] for y in range(h)]
    # 只留最大的一块（跑道）；起点附近可能有被起跑线、旗子隔开的小块
    sx, sy = round(start_px[0] / scale), round(start_px[1] / scale)
    seen = [[0] * w for _ in range(h)]; best = []
    for y0 in range(h):
        for x0 in range(w):
            if grid[y0][x0] and not seen[y0][x0]:
                comp = [(x0, y0)]; seen[y0][x0] = 1; q = deque([(x0, y0)])
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        X, Y = x + dx, y + dy
                        if 0 <= X < w and 0 <= Y < h and grid[Y][X] and not seen[Y][X]:
                            seen[Y][X] = 1; comp.append((X, Y)); q.append((X, Y))
                if len(comp) > len(best): best = comp
    keep = [[0] * w for _ in range(h)]
    for x, y in best: keep[y][x] = 1
    g = keep
    # Zhang-Suen 细化
    def nb(x, y):
        return [g[y-1][x], g[y-1][x+1], g[y][x+1], g[y+1][x+1], g[y+1][x], g[y+1][x-1], g[y][x-1], g[y-1][x-1]]
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            kill = []
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if not g[y][x]: continue
                    p = nb(x, y); B = sum(p)
                    if not 2 <= B <= 6: continue
                    A = sum(1 for i in range(8) if p[i] == 0 and p[(i + 1) % 8] == 1)
                    if A != 1: continue
                    if step == 0 and (p[0] * p[2] * p[4] or p[2] * p[4] * p[6]): continue
                    if step == 1 and (p[0] * p[2] * p[6] or p[0] * p[4] * p[6]): continue
                    kill.append((x, y))
            for x, y in kill: g[y][x] = 0
            changed = changed or bool(kill)
    sk = [(x, y) for y in range(h) for x in range(w) if g[y][x]]
    s0 = min(sk, key=lambda p: (p[0] - sx) ** 2 + (p[1] - sy) ** 2)
    # 从起点沿中线做广度优先，走到距离最远、而且在最上面的那一端（终点拱门方向）
    prev = {s0: None}; dist = {s0: 0}; q = deque([s0])
    while q:
        c = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (c[0] + dx, c[1] + dy)
                if n != c and 0 <= n[0] < w and 0 <= n[1] < h and g[n[1]][n[0]] and n not in prev:
                    prev[n] = c; dist[n] = dist[c] + 1; q.append(n)
    far = max(dist, key=lambda p: dist[p] - 0.0 * p[1])
    path = []; c = far
    while c is not None:
        path.append(c); c = prev[c]
    path.reverse()
    pts = [(x * scale + scale / 2, y * scale + scale / 2) for x, y in path]
    k = 6   # 平滑
    return [(sum(p[0] for p in pts[max(0, i - k):i + k + 1]) / len(pts[max(0, i - k):i + k + 1]),
             sum(p[1] for p in pts[max(0, i - k):i + k + 1]) / len(pts[max(0, i - k):i + k + 1])) for i in range(len(pts))]


def track_mask(canvas):
    """按颜色找出 AI 画的跑道（偏红的橙色，包括被建筑物影子盖住的部分），再做一次闭运算填上细的分道线。"""
    px = canvas.load(); m = Image.new('L', canvas.size, 0); mp = m.load()
    for y in range(canvas.height):
        for x in range(canvas.width):
            r, g, b = px[x, y][:3]
            if r > 150 and 65 < g < 165 and 45 < b < 140 and r - g > 55 and r - b > 75:   # 也认在阴影里、颜色深一点的跑道
                mp[x, y] = 255
    # 闭运算：先膨胀再腐蚀，把 8 像素以内的白色分道线缝起来，跑道连成一整块
    return m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))


def trace_path(canvas, g, step=4, reach=70, gap=16):
    """沿着游戏里的理想路线，每隔 step 个地图单位往两侧找画出来的跑道，取跑道中线。返回地图单位的折线。"""
    import math
    mask = track_mask(canvas); mp = mask.load(); Wp, Hp = mask.size
    send = g['send']; off = g['off_y']; pts = []; offs = []
    s = 0.0
    while True:
        s = min(s, send)
        x, y = G.road_pt(s); y += off
        x2, y2 = G.road_pt(min(send, s + 1)); x1, y1 = G.road_pt(max(0, s - 1))
        dx, dy = x2 - x1, (y2 - y1); L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
        hits = []
        for t in range(-reach * 3, reach * 3 + 1):            # 1/3 单位一步
            tu = t / 3; X = round((x + nx * tu) * G.S); Y = round((y + ny * tu) * G.S)
            hits.append(0 <= X < Wp and 0 <= Y < Hp and mp[X, Y] > 0)
        runs, i = [], 0                                       # 连续的跑道段（允许分道线造成的小缺口）
        while i < len(hits):
            if hits[i]:
                j = i; last = i
                while j < len(hits) and (hits[j] or j - last <= gap):
                    if hits[j]: last = j
                    j += 1
                runs.append((i, last)); i = j
            else:
                i += 1
        center = len(hits) // 2; best = None
        for a, b in runs:
            if b - a < 30 * 3: continue                       # 太窄的不是跑道
            d = 0 if a <= center <= b else min(abs(a - center), abs(b - center))
            if best is None or d < best[0]: best = (d, (a + b) / 2 - center)
        offs.append(best[1] / 3 if best and best[0] < 20 * 3 else None)
        pts.append((x, y, nx, ny))
        if s >= send: break
        s += step
    # 缺的用前后插值，再做平滑
    known = [i for i, o in enumerate(offs) if o is not None]
    for i, o in enumerate(offs):
        if o is None:
            lo = max([k for k in known if k < i], default=None); hi = min([k for k in known if k > i], default=None)
            offs[i] = offs[lo] if hi is None else offs[hi] if lo is None else offs[lo] + (offs[hi] - offs[lo]) * (i - lo) / (hi - lo)
    sm = []
    for i in range(len(offs)):
        w = sorted(offs[max(0, i - 4):i + 5]); med = w[len(w) // 2]
        sm.append(med)
    sm = [sum(sm[max(0, i - 6):i + 7]) / len(sm[max(0, i - 6):i + 7]) for i in range(len(sm))]
    return [(round(x + nx * o, 1), round(y + ny * o, 1)) for (x, y, nx, ny), o in zip(pts, sm)], sm


def trim(path, head, tail):
    """把折线两头各剪掉一段（按弧长，地图单位）。"""
    import math
    def cut_front(pts, d):
        acc = 0
        for i in range(len(pts) - 1):
            L = math.dist(pts[i], pts[i + 1])
            if acc + L >= d:
                t = (d - acc) / L
                p = (round(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, 1), round(pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t, 1))
                return [p] + pts[i + 1:]
            acc += L
        return pts
    return cut_front(cut_front(path, head)[::-1], tail)[::-1]


def cells_on(path, n):
    """在折线上按弧长等距放 n 个格子（和游戏里一样）。"""
    import math
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]; total = sum(seg); out = []
    for k in range(n):
        target = total * k / (n - 1); acc = 0
        for i, L in enumerate(seg):
            if acc + L >= target or i == len(seg) - 1:
                t = (target - acc) / L if L else 0
                out.append((path[i][0] + (path[i + 1][0] - path[i][0]) * t, path[i][1] + (path[i + 1][1] - path[i][1]) * t)); break
            acc += L
    return out


def install_extras(canvas, g, path):
    """装进游戏：跑道中线数据（js/map-paths.js）和从地图上裁的三张小图（起跑线、终点拱门、领奖台）。"""
    pts = path[::3] + ([path[-1]] if (len(path) - 1) % 3 else [])
    js = ('/* 由 tools/build_sports.py 生成：长棋盘运动会地图上画出来的跑道中线（地图单位，宽 400）。游戏沿这条线等距摆格子。 */\n'
          'const MAP_PATHS = {\n  long: { H: %d, path: [%s] }\n};\n') % (g['H'], ','.join('[%s,%s]' % (x, y) for x, y in pts))
    with open(os.path.join(G.ROOT, 'js', 'map-paths.js'), 'w', encoding='utf-8') as fo:
        fo.write(js)
    out = os.path.join(G.OUT_PROPS, 'sports'); os.makedirs(out, exist_ok=True)
    rgb = canvas.convert('RGB')
    for name, box in CROPS.items():
        rgb.crop(box).save(os.path.join(out, f'{name}.webp'), 'WEBP', quality=86)
    print('跑道数据', len(pts), '个点 → js/map-paths.js；小图 →', out)


def main():
    g = G.map_geo(G.MAPS['long']); Hpx = round(g['H'] * G.S)
    canvas = fix_joins(composite(Hpx))
    sk = skeleton_path(track_mask(canvas), G.P(g['road'][0]))
    end = min(range(len(sk)), key=lambda i: (sk[i][0] - FINISH[0]) ** 2 + (sk[i][1] - FINISH[1]) ** 2)
    sk = sk[:end + 1]                       # 到终点线就停，最后一格正好在终点线上
    path = trim([(round(x / G.S, 1), round(y / G.S, 1)) for x, y in sk[::2]], START_TRIM, END_TRIM)
    import json
    os.makedirs(os.path.join(G.ROOT, 'art-src', 'preview'), exist_ok=True)
    with open(os.path.join(G.ROOT, 'art-src', 'preview', 'long-sports-path.json'), 'w') as fo:
        json.dump({'H': g['H'], 'path': path}, fo)
    if '--install' in sys.argv:
        install_extras(canvas, g, path)
    print('跑道中线', len(path), '个点；起点', path[0], '终点', path[-1])
    if '--install' in sys.argv:
        out = os.path.join(G.OUT_MAPS, 'map-long-sports.webp')
    else:
        out = os.path.join(G.ROOT, 'art-src', 'preview', 'map-long-sports.webp')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.convert('RGB').save(out, 'WEBP', quality=82, method=6)
    print('完成', out, canvas.size)


if __name__ == '__main__':
    main()
