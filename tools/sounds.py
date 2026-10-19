# -*- coding: utf-8 -*-
"""用 Kie.ai 的 Suno「生成声音」模型做事件卡和道具的真实音效，存到 sounds/<名字>.mp3。

运行：IMAGE_PROVIDER=kie .venv/bin/python tools/sounds.py [名字…] [--force]
原始结果（每次两个版本）缓存在 art-src/sounds/，挑好的那个再复制到 sounds/。
"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_art as G

ROOT = G.ROOT
RAW = os.path.join(ROOT, 'art-src', 'sounds')

# 只要音效，不要音乐和人声唱歌
TAIL = ' Short game sound effect only, about 2-4 seconds, no music, no singing, no speech, no words. Clean, punchy, kid-friendly.'
SOUNDS = {
    'cheer3': ('Short 5-second kids cartoon victory celebration with a natural ending: bouncy happy brass, xylophone and drum roll, '
               'plus a crowd of tiny cartoon animals cheering in squeaky high-pitched chipmunk voices "yaaay! woo-hoo!" with claps, '
               'ending on a joyful "ta-da!". No adult or male voices, no singing, no words.'),
    'cheer2': ('A complete short victory celebration, about 5 seconds, with a natural ending, for a little kids\' cartoon: a bright, '
               'bouncy, happy celebration tune with cheerful brass and xylophone and a fun drum roll, mixed with a big excited crowd '
               'cheering "yaaay!" and clapping, building up to a joyful final "ta-da!" hit with confetti poppers. Super cheerful and '
               'playful. No singing, no words.'),
    'splash3': ('One single very short sound effect, about 1 second: just one simple, clean cartoon SPLASH of something falling into '
                'water. Nothing else — no voice, no slip, no music, no melody, no background sound.'),
    'splash2': ('One single complete short sound effect, under 3 seconds, with a natural ending: a cartoon banana-peel slip "squeeeak", '
                'a silly surprised "whoa!" yelp, then a big funny SPLASH into water with a few bubbly blub-blubs. Playful and '
                'exaggerated, for little kids. Sound effect only, no music, no melody, no background music.'),
    'portalFail4': ('One single very short sound effect, under 2 seconds, with a natural ending: just a classic cartoon sad trombone '
                    '"wah-wah-wah-waaah" sliding down in a funny, exaggerated disappointed way. Nothing else — no music box, no '
                    'shimmer, no other music, no drums, no singing. Cute for little kids.'),
    'portalFail3': ('One complete short sound effect, about 2-3 seconds, with a natural ending: a magical portal that fails to open, in a '
                    'very exaggerated, funny, DISAPPOINTED cartoon way — a soft shimmer sputters and fizzles out, then a classic '
                    'cartoon "sad trombone" style "wah-wah-wah-waaah" sliding down, ending with a deflated little "pfft". Over-the-top '
                    'comic disappointment, cute for little kids, not scary. No drums, no singing.'),
    'portalFail2': ('One complete short sound effect, about 2 seconds, with a natural ending: a gentle magical portal that fails to open — '
                    'a soft shimmer that fizzles out, with a few sweet music-box notes going down in a cute "aww, not this time" way. '
                    'Soft and gentle, cartoon style for little kids, not scary. Just a tiny touch of melody, no drums, no singing.'),
    'portal3': ('One complete short sound effect, about 2-3 seconds, with a natural ending: a gentle, soft magical time-travel portal — '
                'a smooth, dreamy rising shimmer-whoosh (not harsh or loud) carried by a few soft, sweet music-box or celesta notes '
                'that rise up and resolve into a warm sparkly "pling" at the end. Soft, magical and soothing, cartoon style for little '
                'kids. Just a tiny touch of melody, no drums, no singing.'),
    'portal2': ('One single complete short sound effect, under 3 seconds, with a natural ending: a sci-fi teleport ZAP — a fast rising '
                'electronic warp whoosh that ends in a bright sparkly "pling". Cartoon, playful, for little kids. Sound effect only, '
                'no music, no melody, no background music.'),
    'unicorn2': ('One single complete short sound effect, about 3 seconds, with a natural ending: a happy cartoon unicorn neighs a bright, '
                 'cheerful whinny, then glittering magical sparkles and a soaring whoosh as it flies up into the sky and fades away. '
                 'Playful, for little kids. Sound effect only, no music, no melody, no background music.'),
    'coach3': ('One single complete short sound effect, exactly about 3 seconds long, with a natural ending: first a delightful, '
               'happy magical sparkle — a bright twinkly fairy-godmother wand chime "ting-a-ling" — then cheerful clip-clop horse '
               'hooves trotting with jingling harness bells as a magic pumpkin carriage rolls away and fades out. Playful, for little '
               'kids. Sound effect only, no music, no melody, no background music.'),
    'coach2': ('One single complete short sound effect, about 3 seconds, with a natural ending: a fairy-tale carriage passing by — '
               'cheerful clip-clop horse hooves and jingling harness bells that pass and fade away into the distance. Playful, for '
               'little kids. Sound effect only, no music, no melody, no background music.'),
    'rest2': ('One single complete short sound effect, about 2 seconds, with a natural ending: one big funny cartoon snore — a rumbly '
              'inhale and a whistling squeaky exhale that ends softly. Cute and playful, for little kids. Sound effect only, no music, '
              'no melody, no background music.'),
    'mush3': ('One single complete short sound effect, under 3 seconds, with a natural ending: a cute cartoon tummy rumbling and '
              'gurgling softly "grrr-rumble", together with a little cartoon character\'s sad, sickly moan "ohhh-nooo... uhhh" like a '
              'kid with a tummy ache. Soft, cute and gentle cartoon style for little kids — NOT gross: no burps, no farts, no vomiting '
              'sounds. Sound effect only, no music, no melody, no background music.'),
    'castle2': ('A complete short royal victory fanfare, 5 to 6 seconds long, with a natural ending: bold bright trumpets and festive '
                'booming drums play a triumphant, exciting castle celebration that keeps building up — getting bigger, louder and more '
                'thrilling — and ends on a grand, glorious final peak chord with cymbals crashing and fireworks bursting. Cheerful '
                'fairy-tale style for little kids. No singing, no voices.'),
    # 第二轮：一个一个调试的完整短音效（不截断）
    'mush2': ('One single complete short sound effect, under 3 seconds, with a natural ending: a cartoon character feels sick after eating a '
              'poison mushroom — a dizzy, woozy wobble sound, a loud funny tummy gurgle "grrrumble-blorp", and a queasy little "urrp" '
              'that fades out naturally. Cute cartoon style for little kids, not gross. Sound effect only, no music, no melody, no '
              'background music.'),
    # 恶龙：用户自己写的描述（已选定版本 4 前 3 秒 → sounds/dragon.m4a）
    'roar2': ('A goofy cartoon monster dragon breathing a dramatic WHOOSH of magical fire, followed by a silly high-pitched voice '
              'yelling and comical fast tiptoe footsteps running away. Playful and exaggerated cartoon sound effects for little kids, '
              '2-3 seconds.'),
    'mush': 'A cartoon wicked witch cackling a sneaky, spooky "hee-hee-hee" laugh with a bubbling cauldron and a magic poof, followed by a silly dizzy "wooo-oo" wobble sound, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'rest': 'A cartoon character snoring loudly and comically — a big rumbly snore followed by a whistling squeaky exhale, then a sleepy mumble, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'coach': 'A magical pumpkin carriage arriving: bright fairy-tale sparkle chimes, then cheerful clip-clop horse hooves trotting fast on cobblestones with jingling harness bells and creaky wooden wheels rolling, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'unicorn': 'A magical unicorn takes off: a happy whinny, a glittering harp swirl of magic sparkles, then a soaring whoosh flying up into the sky, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'portal': 'A cartoon time-travel portal: a rising sci-fi warp hum that spins faster and faster, a bright electronic "zwoop" as someone zooms through time, ending with a sparkly arrival ping, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'portalFail': 'A cartoon magic portal that fizzles out: a sputtering electronic buzz, a sad descending "whomp-whomp" power-down, and a tiny comic puff of smoke, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'castle': 'A royal castle victory celebration: bold trumpets blowing a short triumphant fanfare with booming festive drums, followed by fireworks whistling up and bursting with crackles and pops, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'splash': 'A cartoon runner slips on a banana peel: a squeaky slip-and-skid, a silly high-pitched "whoa-oh!" yell, then a big comical SPLASH into water followed by a few bubbly blub-blub sounds, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'icecream': 'A cheerful ice cream truck pulling up: a happy music-box ice-cream-truck jingle, a bell "ding-ding", and a delighted "mmm!" slurp of a cone, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'queue': 'Waiting impatiently in a long line: a clock going tick-tock, a cartoon foot tapping faster and faster, then a long bored sigh, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'boing': 'A cartoon trampoline bounce: a big springy "BOING-oing-oing" as someone bounces super high, a whoosh in the air, and a bouncy landing, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'juice': 'Drinking a magic energy juice: a long loud slurp through a straw, a funny "ahhh!" refreshed gasp, then a zippy power-up sound and a cartoon speed zoom as the runner dashes off, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'glide': 'Paragliding take-off: a quick running patter, a big flappy swoosh as the paraglider wing fills with air, then rushing wind and a gleeful "wheee!" while soaring, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'gust': 'A howling cartoon gust of wind that blows the paraglider back: a whooshing gust, a flappy fabric flutter, and a little disappointed "aww" boing, playful and exaggerated sound effects for little kids, 2-3 seconds.',
    'cheer': 'Winning a cartoon race: a sharp referee whistle, a big stadium crowd cheering and clapping wildly, and a celebratory "ta-da!" trumpet flourish with confetti poppers, playful and exaggerated sound effects for little kids, 2-3 seconds.',
}


OWN_PROMPT = set(SOUNDS)   # 每条都是完整描述（2026-10-18 和用户一起定的），不再加通用结尾


def download(url, path):
    with urllib.request.urlopen(url, timeout=300) as r, open(path, 'wb') as f:
        f.write(r.read())


def gen(name):
    os.makedirs(RAW, exist_ok=True)
    task = G.kie_call('/api/v1/jobs/createTask', {'model': 'ai-music-api/sounds',
                      'input': {'prompt': SOUNDS[name] + ('' if name in OWN_PROMPT else TAIL), 'model': 'V6', 'sound_loop': False}}, f'snd-{name}')['taskId']
    wait, t0 = 5, time.time()
    while True:
        time.sleep(wait); wait = min(wait + 3, 20)
        d = G.kie_call(f'/api/v1/jobs/recordInfo?taskId={task}', None, f'snd-{name}')
        st = d.get('state')
        if st == 'success':
            resp = d.get('response') or json.loads(d.get('resultJson') or '{}')
            clips = (resp.get('data') if isinstance(resp, dict) else None) or resp.get('resultUrls') or []
            paths = []
            for i, c in enumerate(clips):
                url = c.get('audio_url') if isinstance(c, dict) else c
                if not url: continue
                p = os.path.join(RAW, f'{name}-{i + 1}.mp3'); download(url, p); paths.append(p)
            print('完成', name, [os.path.basename(p) for p in paths], [c.get('duration') for c in clips if isinstance(c, dict)])
            return paths
        if st == 'fail':
            print('失败', name, d.get('failCode'), d.get('failMsg')); return []
        if time.time() - t0 > 900:
            print('超时', name, task); return []


def gen4(name):
    # 每次任务给两个版本；做两次，存成 -1..-4
    first = gen(name)
    keep = []
    for i, p in enumerate(first):
        q = os.path.join(RAW, f'{name}-tmp{i}.mp3'); os.replace(p, q); keep.append(q)
    second = gen(name)
    for i, p in enumerate(second):
        os.replace(p, os.path.join(RAW, f'{name}-{i + 3}.mp3'))
    for i, q in enumerate(keep):
        os.replace(q, os.path.join(RAW, f'{name}-{i + 1}.mp3'))


if __name__ == '__main__':
    names = [a for a in sys.argv[1:] if a in SOUNDS] or [k for k in SOUNDS if k != 'roar2']
    force = '--force' in sys.argv
    for n in names:
        if not force and os.path.exists(os.path.join(RAW, f'{n}-4.mp3')):
            print('跳过', n); continue
        print('  做', n, '…'); gen4(n)
