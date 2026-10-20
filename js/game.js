(function(){
/* ---------- data ---------- */
const LIB300 = '一二三四五六七八九十百千万两半几人爸妈爷奶哥姐弟妹儿子女男孩家朋友老师生王公主宝口目耳手足头发牙眼鼻心身脚脸力日月天地山水火土石田风雨云雪电星光江河海林木花草树叶竹禾虹马牛羊鸟鱼虫猫狗鸡鸭猪兔龙虎象熊猴蛇羽毛红黄蓝绿白黑紫色彩金米饭面菜果瓜苹茶蛋糖汤吃喝饼豆肉门车船书本包衣服帽笔刀尺桌床灯球画字纸杯碗窗房玩上下左右前后里外中东西南北边国城路园桥年今明早晚午时候春夏秋冬夜节来去走跑跳飞坐站看见听说话读写唱歌笑哭开打拿放洗跟找买做给叫想爱要会能出进回到起用住大小多少长短高低远近快慢好坏新旧美丽冷热甜香真乐喜欢怕气学校课文问答名同我你他她它们的了是不在有和也都很吗呢吧这那什么谁哪个只没就还又再把对啊';
const COLORS = ['#E2475B','#3B86E6','#2EAE70','#F0862A','#9A68DE','#DE4CA2'];
// Creature avatars (art-src/avatars, tools/avatars.py): stored on players as 'c:<key>'; emoji avatars are stored as the emoji itself.
const CREATURES = {
  axolittle:{zh:'喵喵螈', en:'Axolo-meow'}, hippofly:{zh:'大嘴蝶', en:'Hippoflutter'}, seacoon:{zh:'小贼蜥', en:'Sneaky Lizcoon'},
  dragoink:{zh:'喷火猪猪', en:'Dragoink'}, octowl:{zh:'八爪咕咕', en:'Octo-hoot'}, unicwhale:{zh:'独角鲸鲸', en:'Splashcorn'},
  ladyfrog:{zh:'瓢瓢蛙', en:'Ladyhop'}, snoala:{zh:'慢吞吞', en:'Koalasnail'},
  squirrot:{zh:'嘴硬鹦', en:'Nutty Polly'}, poodlephant:{zh:'嘟嘟卷', en:'Trunk-a-Doodle'}
};
const CREATURE_AVS = Object.keys(CREATURES).map(k => 'c:' + k);
const creatureOf = a => typeof a === 'string' && a.startsWith('c:') ? CREATURES[a.slice(2)] : null;
const avHTML = a => creatureOf(a) ? `<img class="avimg" src="images/avatars/${a.slice(2)}.webp" alt="${creatureOf(a).zh}" draggable="false">` : esc(a || '🙂');
const LIMITS = {dragon:[0,4], mush:[0,4], coach:[0,4], bridge:[0,5], uni:[0,8]};
const LENS = [20, 28, 36];
// Each board length is shown to players as a theme to pick (the long board is the sports-day map).
const BOARD_CHOICES = {
  20: {zh:'童话森林', en:'Fairy Forest', subZh:'短途', subEn:'Short', img:'images/props/castle.webp'},
  28: {zh:'童话森林', en:'Fairy Forest', subZh:'长途', subEn:'Long', img:'images/props/castle.webp'},
  36: {zh:'动物运动会', en:'Animal Sports Day', subZh:'', subEn:'', img:'images/props/sports/theme.webp'}
};
const KEY_S = 'szsxq.settings.v2', KEY_G = 'szsxq.game.v2';
const RM = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);

const app = document.getElementById('app');
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = n => Math.floor(Math.random() * n);
const shuffleArr = a => { for (let i = a.length - 1; i > 0; i--) { const j = rnd(i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const load = k => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } };
const store = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
const hanOf = t => String(t).match(/\p{Script=Han}/gu) || [];
const uniq = a => [...new Set(a)];
function mulberry32(a){ return function(){ a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

/* ---------- board logic ---------- */
const DRAGON_ZONE = 2 / 3;  // dragons only appear in the first 2/3 of the path — meeting one near the castle is too discouraging
const DOOR_MAX = 6;         // auto-placed magic doors: exit at most 6 cells after the entrance (players may move them further by hand)
function genBoard(chars, c, uniPref){
  const m = chars.length + c.dragon + c.mush + c.coach;
  const jlo = Math.min(2, m - 1), jhi = Math.max(jlo, m - 2);
  const taken = new Map();
  // spread the given specials evenly over slots a..b, nudging each to the nearest free slot away from other specials
  const spread = (types, a, b) => {
    const k = types.length, span = b - a + 1;
    types.forEach((t, q) => {
      const lo = a + Math.floor(q * span / k), hi = a + Math.floor((q + 1) * span / k) - 1;
      const want = lo + rnd(Math.max(1, hi - lo + 1));
      let best = -1, bs = Infinity;
      for (let j = a; j <= b; j++){
        if (taken.has(j)) continue;
        const sc = Math.abs(j - want) + (taken.has(j - 1) || taken.has(j + 1) ? 3 : 0);
        if (sc < bs){ bs = sc; best = j; }
      }
      if (best >= 0) taken.set(best, t);
    });
  };
  spread(Array(c.dragon).fill('dragon'), jlo, Math.max(jlo, Math.min(jhi, Math.floor(m * DRAGON_ZONE) - 1)));
  spread(shuffleArr([].concat(Array(c.mush).fill('mush'), Array(c.coach).fill('coach'))), jlo, jhi);
  const cells = [{t:'start'}];
  let ci = 0;
  for (let j = 0; j < m; j++) cells.push(taken.has(j) ? {t: taken.get(j)} : {t:'char', ch: chars[ci++]});
  cells.push({t:'end'});
  const total = cells.length;
  const charIdx = cells.map((x, i) => x.t === 'char' ? i : -1).filter(i => i >= 0);
  const used = new Set(), bridges = [];
  for (let tries = 0; bridges.length < c.bridge && tries < 600; tries++){
    const from = charIdx[rnd(charIdx.length)];
    if (used.has(from)) continue;
    const cands = charIdx.filter(to => to - from >= 5 && to - from <= DOOR_MAX && to < total - 1 && !used.has(to));
    if (!cands.length) continue;
    const to = cands[rnd(cands.length)];
    if ([...used].some(u => Math.abs(u - from) < 3 || Math.abs(u - to) < 3)) continue;
    used.add(from); used.add(to); bridges.push({from, to});
  }
  const pref = new Set(uniPref || []);
  const elig = charIdx.filter(i => !used.has(i));
  const ordered = shuffleArr(elig.filter(i => pref.has(cells[i].ch))).concat(shuffleArr(elig.filter(i => !pref.has(cells[i].ch))));
  ordered.slice(0, c.uni).forEach(i => cells[i].uni = true);
  return { cells, bridges };
}
const boardChars = b => b.cells.filter(c => c.t === 'char').map(c => c.ch);
const uniChars = b => b.cells.filter(c => c.uni).map(c => c.ch);
const bridgeEnds = b => new Set(b.bridges.flatMap(l => [l.from, l.to]));

/* ---------- illustrations ---------- */
/* ---------- themes: each board's map decides its pictures and wording ---------- */
// Prop keys stay the same in the game logic (dragon = back to start, mush = skip a turn, coach = +2,
// uni = read for +3, bridge/portal/door = read two characters to jump); only the story around them changes.
const THEMES = {
  forest: {
    sfx: { dragon:'file:dragon', mush:'file:poison', skip:'file:poison', coach:'file:carriage', uni:'file:unicorn', door:'file:portal', doorFail:'file:gust', win:'file:castle' },
    art: { dragon:'images/props/dragon.webp', mush:'images/props/mush.webp', coach:'images/props/coach.webp',
      unicorn:'images/props/unicorn.webp', portal:'images/props/door-open.webp', door:'images/props/door-closed.webp',
      start:'images/props/forest.webp', end:'images/props/castle.webp', win:'images/props/castle.webp' },
    en: { dragon:'Dragon', mush:'Poison Mushroom', coach:'Pumpkin Coach', coachS:'Coach', uni:'Unicorn', door:'Magic Door', from:'entrance', to:'exit', end:'Castle',
      subtitle:'Start in the forest and read your way to the castle', toTop:'Scroll up to see the castle.',
      ruleGoal:'Take turns rolling the die. Start in the forest — the first one to reach the castle wins!',
      ruleDragon:'Dragon: it scares you all the way back to the start!', ruleMush:'Poison Mushroom: tummy ache — skip your next turn.',
      ruleCoach:'Pumpkin Coach: ride 2 more spaces forward.', ruleUni:'Unicorn: read this character right and fly 3 spaces forward.',
      ruleDoor:'Magic Door: read the character on the open door, then the one on the closed door with the same number, to go through.',
      dragonCard: n => ({title:'Here comes the dragon!', text:`${n} got scared by the dragon and runs back to the start.`, btn:'Run home'}),
      mushCard: n => ({title:'Poison mushroom!', text:`${n} has a tummy ache and must skip the next turn.`, btn:'Got it'}),
      skipCard: n => ({title:'Resting this turn', text:`${n} ate a poison mushroom and can't roll this turn.`, btn:'Next player'}),
      coachCard: {title:'Hop in the pumpkin coach!', text:'The coach carries you 2 more spaces forward.', btn:'Let\'s go!'},
      uniHint:'There\'s a unicorn on this character! Read it right to fly 3 spaces forward.',
      uniCard: {title:'You got it!', text:'The unicorn flies you 3 spaces forward.', btn:'Fly!'},
      doorHint: k => `This is magic door ${k}! Read this character, then the one at the other end of the door, to go through.`,
      doorHint2: (k, to) => `Great! Now read the character at the other end of door ${k} (space ${to}) to go through.`,
      doorCard: (n, to) => ({title:'Through the magic door!', text:`${n} jumps straight to space ${to}.`, btn:'Go!'}),
      doorFail: {title:'So close!', text:'The door won\'t open this time — stay on this space.'},
      backHome:'This time, go back to the start.',
      winMsg: n => `${n} reached the castle!`, winCard: n => ({title:`${n} reached the castle!`, text:'First one to the castle — amazing!'}) },
    t: { dragon:'恶龙', mush:'毒蘑菇', coach:'南瓜马车', coachS:'马车', uni:'独角兽', door:'魔法门', from:'入口', to:'出口', end:'城堡',
      subtitle:'从森林出发，读着汉字走到城堡', toTop:'往上滑能看到城堡。',
      ruleGoal:'大家轮流掷骰子，从森林出发，谁先走到城堡谁就赢。',
      ruleDragon:'恶龙：被吓跑了，回到森林出发点。', ruleMush:'毒蘑菇：下一轮休息，不能掷骰子。',
      ruleCoach:'南瓜马车：直接再往前走两格。', ruleUni:'独角兽：读对这个字，往前飞三格。',
      ruleDoor:'魔法门：读对开着的门上的字，再读对同号关着的门上的字，就能穿过去。',
      dragonCard: n => ({title:'恶龙来啦！', text:`${n} 被恶龙吓跑了，要回到森林出发点。`, btn:'跑回森林'}),
      mushCard: n => ({title:'毒蘑菇！', text:`${n} 下一轮要休息，不能掷骰子。`, btn:'知道了'}),
      skipCard: n => ({title:'休息一轮', text:`${n} 吃了毒蘑菇，这一轮不能掷骰子。`, btn:'下一位'}),
      coachCard: {title:'坐上南瓜马车！', text:'马车载着你，直接再往前走两格。', btn:'出发！'},
      uniHint:'这个字上有独角兽！读对了，可以往前飞三格。',
      uniCard: {title:'读对啦！', text:'独角兽载着你往前飞三格。', btn:'飞！'},
      doorHint: k => `这一格有 ${k} 号魔法门！读对这个字，再读对门另一头的字，就能穿过去。`,
      doorHint2: (k, to) => `读对了！再读出 ${k} 号门另一头的这个字（第 ${to} 格），就能穿过去。`,
      doorCard: (n, to) => ({title:'穿过魔法门！', text:`${n} 直接到第 ${to} 格。`, btn:'走过去！'}),
      doorFail: {title:'差一点点！', text:'这次穿不过魔法门，留在原来这一格。'},
      backHome:'这次要回到森林出发点。',
      winMsg: n => `${n} 到达城堡！`, winCard: n => ({title:`${n} 到达城堡啦！`, text:'第一个走到城堡，太厉害了！'}) }
  },
  sports: {
    art: { dragon:'images/props/sports/splash.webp', mush:'images/props/sports/icecream.webp', coach:'images/props/sports/trampoline.webp',
      unicorn:'images/props/sports/juice.webp', portal:'images/props/sports/glide-up.webp', door:'images/props/sports/glide-down.webp',
      start:'images/props/sports/start.webp', end:'images/props/sports/finish.webp', win:'images/props/sports/podium.webp' },
    sfx: { dragon:'file:splash', mush:'file:icecream', skip:'file:queue', coach:'file:boing', uni:'file:juice', door:'file:glide', doorFail:'file:gust', win:'file:cheer' },
    en: { dragon:'Splash!', mush:'Ice Cream', coach:'Trampoline', coachS:'Trampoline', uni:'Energy Juice', door:'Paraglider', from:'take-off', to:'landing', end:'Finish',
      subtitle:'Start at the starting line and read your way to the finish', toTop:'Scroll up to see the finish line.',
      ruleGoal:'Take turns rolling the die. Start at the starting line — the first one across the finish line wins!',
      ruleDragon:'Splash!: slip on a banana peel into the river and go home to change — back to the start.', ruleMush:'Ice Cream Truck: you can\'t resist lining up for ice cream — skip your next turn.',
      ruleCoach:'Trampoline: bounce up high and jump 2 spaces forward.', ruleUni:'Energy Juice: read this character right, drink up and dash 3 spaces forward.',
      ruleDoor:'Paraglider: read the character at the take-off spot, then the one at the landing spot with the same number, to fly there.',
      dragonCard: n => ({title:'Splash! Into the river!', text:`${n} slipped on a banana peel and fell into the river — back to the start to change clothes.`, btn:'Back to start'}),
      mushCard: n => ({title:'Ice cream truck!', text:`${n} can't resist lining up for ice cream and will skip the next turn.`, btn:'Got it'}),
      skipCard: n => ({title:'Still in line', text:`${n} is still waiting for ice cream and can't roll this turn.`, btn:'Next player'}),
      coachCard: {title:'Jump on the trampoline!', text:'The trampoline bounces you 2 spaces forward!', btn:'Jump!'},
      uniHint:'There\'s energy juice on this character! Read it right to dash 3 spaces forward.',
      uniCard: {title:'You got it!', text:'You drink the energy juice and zoom 3 spaces forward!', btn:'Dash!'},
      doorHint: k => `This is paraglider take-off ${k}! Read this character, then the one at landing spot ${k}, to fly there.`,
      doorHint2: (k, to) => `Great! Now read the character at landing spot ${k} (space ${to}) to take off.`,
      doorCard: (n, to) => ({title:'Take off!', text:`${n} glides all the way to space ${to}.`, btn:'Fly!'}),
      doorFail: {title:'Too windy!', text:'It\'s not a good day to fly — stay on this space.'},
      backHome:'This time, go back to the start.',
      winMsg: n => `${n} crossed the finish line!`, winCard: n => ({title:`${n} crossed the finish line!`, text:'First one across the finish line — amazing!'}) },
    t: { dragon:'掉河里', mush:'冰淇淋车', coach:'蹦床', coachS:'蹦床', uni:'能量果汁', door:'滑翔伞', from:'起飞点', to:'降落点', end:'终点',
      subtitle:'从起跑线出发，读着汉字冲过终点', toTop:'往上滑能看到终点。',
      ruleGoal:'大家轮流掷骰子，从起跑线出发，谁先冲过终点谁就赢。',
      ruleDragon:'掉河里：踩到香蕉皮掉进河里，要回家换衣服，回到起点重新出发。', ruleMush:'冰淇淋车：忍不住去排队买冰淇淋，下一轮停一次。',
      ruleCoach:'蹦床：弹得高高的，直接往前跳两格。', ruleUni:'能量果汁：读对这个字，喝下果汁往前冲三格。',
      ruleDoor:'滑翔伞：读对起飞点上的字，再读对同号降落点上的字，就能飞过去。',
      dragonCard: n => ({title:'扑通！掉河里了！', text:`${n} 踩到香蕉皮，掉进了河里，要回家换衣服，回到起点重新出发。`, btn:'回起点'}),
      mushCard: n => ({title:'冰淇淋车！', text:`${n} 忍不住去排队买冰淇淋，下一轮要停一次。`, btn:'知道了'}),
      skipCard: n => ({title:'还在排队', text:`${n} 还在排队买冰淇淋，这一轮不能掷骰子。`, btn:'下一位'}),
      coachCard: {title:'跳上蹦床！', text:'蹦床把你弹得高高的，直接往前跳两格！', btn:'跳！'},
      uniHint:'这个字旁边有能量果汁！读对了，喝下去往前冲三格。',
      uniCard: {title:'读对啦！', text:'喝下能量果汁，飞快地往前冲三格！', btn:'冲！'},
      doorHint: k => `这一格是 ${k} 号滑翔伞起飞点！读对这个字，再读对 ${k} 号降落点上的字，就能飞过去。`,
      doorHint2: (k, to) => `读对了！再读出 ${k} 号降落点上的这个字（第 ${to} 格），就能起飞。`,
      doorCard: (n, to) => ({title:'起飞啦！', text:`${n} 乘着滑翔伞，飞到第 ${to} 格。`, btn:'飞过去！'}),
      doorFail: {title:'风太大了！', text:'今天不适合起飞，留在原来这一格。'},
      backHome:'这次要回到起点。',
      winMsg: n => `${n} 冲过终点！`, winCard: n => ({title:`${n} 冲过终点啦！`, text:'第一个冲过终点，太厉害了！'}) }
  }
};
// Language: S.lang 'zh' (default) or 'en'. Chinese characters on the cards, pinyin and words in hints stay Chinese either way.
const EN = () => typeof S !== 'undefined' && S && S.lang === 'en';
const L = (zh, en) => EN() ? en : zh;
// Players named after their creature show the creature's English name in English mode.
const nm = p => { const c = creatureOf(p.avatar); return EN() && c && p.name === c.zh ? c.en : p.name; };
let TH = THEMES.forest;
const themeOf = b => THEMES[(b ? mapFor(b.cells.length) : MAPS[1]).theme] || THEMES.forest;
const useTheme = b => { const th = themeOf(b); TH = {...th, t: EN() ? th.en : th.t}; return TH; };
const art = (k, cls, alt) => `<img class="${cls || ''}" src="${TH.art[k]}" alt="${alt || ''}" draggable="false">`;
const RAINBOW_ICON = `<svg viewBox="0 0 60 34" aria-hidden="true"><g fill="none" stroke-width="4.2" stroke-linecap="round">
  <path d="M5 32 A25 25 0 0 1 55 32" stroke="#E9475B"/><path d="M9.2 32 A20.8 20.8 0 0 1 50.8 32" stroke="#FF9A3C"/><path d="M13.4 32 A16.6 16.6 0 0 1 46.6 32" stroke="#FFD43B"/>
  <path d="M17.6 32 A12.4 12.4 0 0 1 42.4 32" stroke="#3FB873"/><path d="M21.8 32 A8.2 8.2 0 0 1 38.2 32" stroke="#4C8DF0"/></g></svg>`;

/* ---------- map geometry: wide switchbacks across the whole width ---------- */
const MW = 400, R = 76, CXL = 106, CXR = 294, SP = 78, TS = 58, LR = CXR - CXL, LT = Math.PI * R, PER = LR + LT, ROW = 2 * R;
function roadPt(s){
  const k = Math.floor(s / PER), q = s - k * PER, y0 = -k * ROW, right = k % 2 === 0;
  if (q < LR) return { x: right ? CXL + q : CXR - q, y: y0, a: right ? 0 : Math.PI };
  const th = (q - LR) / R, cy = y0 - R;
  if (right) return { x: CXR + R * Math.sin(th), y: cy + R * Math.cos(th), a: Math.atan2(-Math.sin(th), Math.cos(th)) };
  return { x: CXL - R * Math.sin(th), y: cy + R * Math.cos(th), a: Math.atan2(-Math.sin(th), -Math.cos(th)) };
}
// Each background is painted (tools/gen_art.py) around a road built for n0 cells; keep MAPS in sync with that script.
// A board with n cells uses the closest map and spreads its cells evenly along that road.
// The long board uses the sports-day map; its cells follow the track painted in the picture (MAP_PATHS, from tools/build_sports.py).
const MAPS = [{k:'short', n0:28, theme:'forest'}, {k:'mid', n0:36, theme:'forest'},
  {k:'long', n0:44, theme:'sports', src:'images/maps/map-long-sports.webp', path:'long'}];
const mapFor = n => n <= 31 ? MAPS[0] : n <= 39 ? MAPS[1] : MAPS[2];
const geoCache = {};
const DCOL = ['#E2478E','#3B86E6','#2EAE70','#F0862A','#9A68DE'];
function pathGeo(n, m, pd){
  const P = pd.path, cum = [0];
  for (let i = 1; i < P.length; i++) cum.push(cum[i - 1] + Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]));
  const total = cum[cum.length - 1];
  const at = d => {
    let i = 1; while (i < P.length - 1 && cum[i] < d) i++;
    const t = (d - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1), [x0, y0] = P[i - 1], [x1, y1] = P[i];
    return { x: x0 + (x1 - x0) * t, y: y0 + (y1 - y0) * t, a: Math.atan2(y1 - y0, x1 - x0) };
  };
  const cells = Array.from({length:n}, (_, i) => at(total * i / (n - 1)));
  const chev = []; for (let i = 0; i < n - 1; i++) chev.push(at(total * (i + .5) / (n - 1)));
  return { H: pd.H, cells, chev, src: m.src };
}
function geo(n){
  if (geoCache[n]) return geoCache[n];
  const m = mapFor(n);
  if (m.path && typeof MAP_PATHS !== 'undefined' && MAP_PATHS[m.path]) return (geoCache[n] = pathGeo(n, m, MAP_PATHS[m.path]));
  const send = (m.n0 - 1) * SP, sp = send / (n - 1);
  let minY = roadPt(send).y;
  for (let s = 0; s < send; s += 6) minY = Math.min(minY, roadPt(s).y);
  const castleBase = 238 + 22, offY = castleBase + 72 - minY, H = Math.round(offY + 162);
  const T = p => ({ x: p.x, y: p.y + offY, a: p.a });
  const cells = Array.from({length:n}, (_, i) => T(roadPt(i * sp)));
  const chev = []; for (let i = 0; i < n - 1; i++) chev.push(T(roadPt((i + .5) * sp)));
  return (geoCache[n] = { H, cells, chev, src: `images/maps/map-${m.k}.webp` });
}

function rainbowSVG(g, l){
  const a = g.cells[l.from], b = g.cells[l.to];
  const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1;
  let nx = -dy / len, ny = dx / len, k = .42 * len;
  if (mx + nx * k < 26 || mx + nx * k > 374){ nx = -nx; ny = -ny; }
  if (mx + nx * k < 26 || mx + nx * k > 374) k = Math.min(k, Math.abs((nx > 0 ? 374 - mx : mx - 26) / (nx || 1)));
  const cx = mx + nx * k, cy = my + ny * k;
  const cols = ['#9B6BE0','#4C8DF0','#3FB873','#FFD43B','#FF9A3C','#E9475B'];
  let s = `<path d="M${a.x} ${a.y} Q${cx} ${cy} ${b.x} ${b.y}" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="44" fill="none" stroke-linecap="round"/>`;
  cols.forEach((c, j) => { const o = (j - 2.5) * 6.2; s += `<path d="M${(a.x + nx * o).toFixed(1)} ${(a.y + ny * o).toFixed(1)} Q${(cx + nx * o * 1.6).toFixed(1)} ${(cy + ny * o * 1.6).toFixed(1)} ${(b.x + nx * o).toFixed(1)} ${(b.y + ny * o).toFixed(1)}" stroke="${c}" stroke-width="6.6" fill="none" stroke-linecap="round" opacity=".92"/>`; });
  return s;
}
function mapHTML(b, opt = {}){
  useTheme(b);
  const n = b.cells.length, g = geo(n), H = g.H;
  let s = `<svg class="mapsvg" viewBox="0 0 ${MW} ${H}" aria-hidden="true"><image href="${g.src}" x="0" y="0" width="${MW}" height="${H}" preserveAspectRatio="none"/>`;
  for (const c of g.chev) s += `<path d="M-4 -6 L4 0 L-4 6" transform="translate(${c.x.toFixed(1)} ${c.y.toFixed(1)}) rotate(${(c.a * 180 / Math.PI).toFixed(1)})" stroke="#B48443" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity=".8"/>`;
  s += '</svg>';
  const doorAt = {};
  b.bridges.forEach((l, j) => { doorAt[l.from] = {k:'portal', n:j + 1, c:DCOL[j % 5]}; doorAt[l.to] = {k:'door', n:j + 1, c:DCOL[j % 5]}; });
  let tiles = '';
  b.cells.forEach((c, i) => {
    const p = g.cells[i], rot = (((i * 53) % 9) - 4) * .7;
    let inner;
    if (c.t === 'start') inner = `<span class="lb big">${L('出发', 'Start')}</span>`;
    else if (c.t === 'end') inner = `<span class="lb big">${TH.t.end}</span>`;
    else if (c.t === 'dragon') inner = `${art('dragon', 'cardimg')}<span class="lb">${TH.t.dragon}</span>`;
    else if (c.t === 'mush') inner = `${art('mush', 'cardimg')}<span class="lb">${TH.t.mush}</span>`;
    else if (c.t === 'coach') inner = `${art('coach', 'cardimg')}<span class="lb">${TH.t.coach}</span>`;
    else inner = `<span class="zi">${esc(c.ch)}</span><span class="num">${i}</span>${c.uni ? art('unicorn', 'uni') : ''}${doorAt[i] ? `<span class="door" style="--dc:${doorAt[i].c}">${art(doorAt[i].k)}<b>${doorAt[i].n}</b></span>` : ''}`;
    const tap = opt.edit && c.t === 'char';
    const tag = tap ? 'button' : 'div';
    const attrs = tap ? ` type="button" data-act="tile" data-i="${i}" aria-label="${L(`第${i}格：`, `Space ${i}: `)}${esc(c.ch)}"` : '';
    tiles += `<${tag} class="tile ${c.t}" style="left:${((p.x - TS / 2) / MW * 100).toFixed(3)}%;top:${((p.y - TS / 2) / H * 100).toFixed(3)}%;--rot:${rot}deg"${attrs}>${inner}</${tag}>`;
  });
  return `<div class="map" id="${opt.game ? 'map' : 'pmap'}">${s}${tiles}<div class="tokens" id="${opt.game ? 'tokens' : ''}"></div></div>`;
}


/* ---------- settings & state ---------- */
// Built-in lists: 300 common characters, plus the next 200 / 700 from hints.js (easiest first).
const COMMON = ['c300', 'c500', 'c1000'];
const commonChars = k => hanOf(LIB300 + (k === 'c300' || typeof LIB_MORE === 'undefined' ? '' : LIB_MORE[k] || ''));
function libChars(){ return S.lib === 'mine' ? (S.mine.chars || []) : commonChars(S.lib); }
function drawBoard(){
  const lib = libChars();
  if (lib.length < 8){ S.board = null; return; }
  const chars = pickChars(lib, Math.min(S.len, lib.length));
  const pref = S.lib === 'mine' ? (S.mine.hard || []) : [];
  S.board = genBoard(chars, S.counts, pref);
}
function rearrange(){ if (!S.board) return; S.board = genBoard(boardChars(S.board), S.counts, uniChars(S.board)); }
// Defaults per board length, tuned for a first game; picking a length loads its defaults.
// Bump SETTINGS_VER to hand returning players the new defaults once.
const DEFAULT_COUNTS = {
  20: {dragon:1, coach:1, mush:0, bridge:1, uni:0},
  28: {dragon:1, coach:2, mush:1, bridge:1, uni:1},
  36: {dragon:1, coach:2, mush:2, bridge:1, uni:1}
}, SETTINGS_VER = 4;
// Hints per player per game: 3, 6 or unlimited ('inf'); in a game an unlimited player has hints = -1.
const HINT_CHOICES = [3, 6, 'inf'];
const defaultCounts = len => ({...(DEFAULT_COUNTS[len] || DEFAULT_COUNTS[28])});
function defaultSettings(){
  const s = { players:[{name:'喵喵螈', avatar:'c:axolittle'}, {name:'大嘴蝶', avatar:'c:hippofly'}], lib:'c300', mine:{chars:[], hard:[], name:''}, len:28,
    counts:defaultCounts(28), hints:true, hintN:3, mute:false, board:null, ver:SETTINGS_VER };
  return s;
}
let S = load(KEY_S);
if (!S || !Array.isArray(S.players) || !S.players.length || !S.counts || !S.mine) S = defaultSettings();
if (S.hints === undefined) S.hints = true;
// Who judges the reading: 'parent' (default) or 'voice' (the game listens: for kids playing alone, or grown-ups who
// don't read Chinese). Listening was the default for a day (S.checkV missing); it misheard too often, so reset once.
if (S.check !== 'voice' || !S.checkV) S.check = 'parent';
S.checkV = 2;
// emoji avatars were removed: give those players a free creature (and its name, if they kept the default name)
S.players.forEach(p => {
  if (creatureOf(p.avatar)) return;
  const av = CREATURE_AVS.find(a => !S.players.some(q => q.avatar === a)) || CREATURE_AVS[0];
  if (/^玩家\d+$/.test(p.name || '') || !(p.name || '').trim()) p.name = creatureOf(av).zh;
  p.avatar = av;
});
if (S.lib !== 'mine' && !COMMON.includes(S.lib)) S.lib = 'c300';
if (!COMMON.includes(S.common)) S.common = S.lib === 'mine' ? 'c300' : S.lib;
if (S.lang !== 'en') S.lang = 'zh';
document.documentElement.lang = S.lang === 'en' ? 'en' : 'zh-CN';
if (!HINT_CHOICES.includes(S.hintN)) S.hintN = 3;
/* ---------- learners: each child's progress, kept on this device (no accounts) ---------- */
// A learner is a person, not a seat: a player seat links to a learner id (S.players[i].learner), so avatars and names
// can change freely. Seats without a learner (grown-ups, friends) are not recorded.
// LP.list: [{id, name, avatar}]; LP.stats[id]: {games, reads, chars: {字: {ok, hint, miss, last, m}}}
//   ok = read right without help, hint = right with help (a hint, or the character was already read out earlier in
//   this game), miss = not read, last = last seen (ms), m = mastered at (0 = not yet),
//   rv = review step (index into REVIEW_DAYS), due = when the next review is due (ms), f = fully learned at (0 = not yet).
const KEY_L = 'szsxq.learners.v1', MASTER_OK = 2, REVIEW_SHARE = 0.2, DAY = 864e5;
// Spaced review of mastered characters: due 3 days after mastering, then 1 week, 3 weeks and 2 months after each
// review read right without help. Passing the 2-month review = fully learned (🏅): no more reviews, and it only fills
// a board when nothing else is left. A miss at any point sends the character back to "learning".
const REVIEW_DAYS = [3, 7, 21, 60];
let LP = load(KEY_L);
if (!LP || !Array.isArray(LP.list) || !LP.stats || typeof LP.stats !== 'object') LP = {list: [], stats: {}};
const saveL = () => store(KEY_L, LP);
const learnerOf = id => (id && LP.list.find(l => l.id === id)) || null;
const lstat = id => LP.stats[id] || (LP.stats[id] = {games: 0, reads: 0, chars: {}});
const isMastered = (id, ch) => { const r = LP.stats[id] && LP.stats[id].chars[ch]; return !!(r && r.m); };
const masteredCount = id => Object.values(lstat(id).chars).filter(r => r.m).length;
const isFull = (id, ch) => { const r = LP.stats[id] && LP.stats[id].chars[ch]; return !!(r && r.m && r.f); };
Object.values(LP.stats).forEach(st => Object.values(st.chars || {}).forEach(r => { if (r.m && !r.due){ r.rv = 0; r.due = r.m + REVIEW_DAYS[0] * DAY; } }));
S.players.forEach(p => { if (p.learner && !learnerOf(p.learner)) p.learner = null; });
// Right without a hint MASTER_OK times = mastered. Missing a mastered character sends it back to "learning".
function recordRead(id, ch, ok, hinted){
  if (!learnerOf(id)) return false;
  const st = lstat(id), r = st.chars[ch] || (st.chars[ch] = {ok: 0, hint: 0, miss: 0, last: 0, m: 0});
  let newly = false; st.reads++; r.last = Date.now();
  const now = Date.now();
  if (!ok){ r.miss++; if (r.m){ r.m = 0; r.ok = Math.min(r.ok, 1); r.rv = 0; r.due = 0; r.f = 0; } }
  else if (hinted) r.hint++;
  else {
    r.ok++;
    if (!r.m && r.ok >= MASTER_OK){ r.m = now; r.rv = 0; r.due = now + REVIEW_DAYS[0] * DAY; newly = true; }
    else if (r.m && !r.f && now >= r.due){   // passed a review: wait longer next time, or fully learned after the last one
      if ((r.rv || 0) >= REVIEW_DAYS.length - 1){ r.f = now; r.due = 0; }
      else { r.rv = (r.rv || 0) + 1; r.due = now + REVIEW_DAYS[r.rv] * DAY; }
    }
  }
  saveL(); return newly;
}
function newLearner(name, avatar){
  const l = {id: 'L' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), name: String(name || '').trim().slice(0, 8) || L('小朋友', 'Learner'), avatar};
  LP.list.push(l); lstat(l.id); saveL(); return l;
}
function listSummary(id, chars){
  const st = LP.stats[id]; let m = 0, l = 0, f = 0;
  chars.forEach(c => { const r = st && st.chars[c]; if (r){ if (r.m){ m++; if (r.f) f++; } else l++; } });
  return {m, l, f, n: chars.length - m - l, total: chars.length};
}
// Characters for a new board: mostly ones the learners at the table haven't mastered yet, plus mastered ones whose
// review is due (most overdue first, up to REVIEW_SHARE of the board). If the list runs out of unmastered characters,
// the board is filled with the mastered ones due soonest. Without learners: a random pick, as before.
function pickChars(lib, n){
  const ids = [...new Set(S.players.map(p => p.learner).filter(learnerOf))];
  if (!ids.length) return shuffleArr(lib.slice()).slice(0, n);
  const done = c => ids.every(id => isMastered(id, c)), full = c => ids.every(id => isFull(id, c));
  const due = c => Math.min(...ids.map(id => isFull(id, c) ? Infinity : LP.stats[id].chars[c].due || 0));
  const fresh = shuffleArr(lib.filter(c => !done(c))), now = Date.now();
  // mastered but still in review (soonest due first), then fully learned ones as the very last filler
  const old = lib.filter(c => done(c) && !full(c)).sort((a, b) => due(a) - due(b)).concat(shuffleArr(lib.filter(full)));
  const nDue = old.filter(c => due(c) <= now).length;
  const nOld = Math.min(old.length, Math.max(n - fresh.length, Math.min(nDue, Math.round(n * REVIEW_SHARE))));
  return shuffleArr(fresh.slice(0, n - nOld).concat(old.slice(0, nOld)));
}
if (S.ver !== SETTINGS_VER){ S.counts = defaultCounts(S.len); S.ver = SETTINGS_VER; S.board = null; }
if (!S.board || !Array.isArray(S.board.cells)) { drawBoard(); }
let G = load(KEY_G);
if (G && (!G.board || !Array.isArray(G.players))) G = null;
const saveS = () => store(KEY_S, S);
const saveG = () => store(KEY_G, G);
saveS();

let screen = (G && G.active) ? 'game' : 'setup';
let ui = { openAv:-1, openWho:-1, pasting:false, libMsg:'', libErr:'', progId:null, progLib:null };
let busy = false;

/* ---------- sound & speech ---------- */
let AC = null;
// Phones only allow sound after a tap, and iPhone Safari mutes Web Audio when the ring/silent switch is on.
// So: ask for "playback" audio (Safari 16.4+), and on every tap create/resume the AudioContext and play a tiny silent sound.
let micBusy = false;   // true while listening: leave the audio session alone so the microphone works (iPhone)
function ac(){
  try { if (!micBusy && navigator.audioSession && navigator.audioSession.type !== 'playback') navigator.audioSession.type = 'playback'; } catch (e) {}
  if (!AC){ try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { AC = null; } }
  if (AC && AC.state !== 'running') AC.resume().catch(() => {});
  return AC;
}
let unlockedAudio = false;
function unlockAudio(){
  const a = ac(); if (!a) return;
  if (!unlockedAudio){
    try { const src = a.createBufferSource(); src.buffer = a.createBuffer(1, 1, 22050); src.connect(a.destination); src.start(0); unlockedAudio = true; } catch (e) {}
    Object.keys(SOUND_FILES).forEach(loadSound);
    // older iPhones (no navigator.audioSession): a playing <audio> element switches the page out of "silent switch" mode
    if (!navigator.audioSession && /iP(hone|ad|od)|Macintosh/.test(navigator.userAgent) && 'ontouchend' in document){
      try {
        const el = new Audio('data:audio/wav;base64,UklGRnAEAABXQVZFZm10IBAAAAABAAEAESsAABErAAABAAgAZGF0YUwEAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==');
        el.loop = true; el.volume = 0.01; el.setAttribute('playsinline', ''); el.play().catch(() => {});
      } catch (e) {}
    }
  }
}
['pointerdown', 'touchend', 'click', 'keydown'].forEach(t => document.addEventListener(t, unlockAudio, {capture: true, passive: true}));
document.addEventListener('visibilitychange', () => { if (!document.hidden && AC && AC.state !== 'running') AC.resume().catch(() => {}); });
function tone(f, t0, dur, type, vol){
  const a = AC, t = a.currentTime + t0, o = a.createOscillator(), g = a.createGain();
  o.type = type || 'sine'; o.frequency.setValueAtTime(f, t);
  g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(vol || .12, t + .012); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
  o.connect(g); g.connect(a.destination); o.start(t); o.stop(t + dur + .03);
}
/* little synth helpers (no audio files: every effect is generated) */
function glide(f0, f1, t0, dur, type, vol, vib){
  const a = AC, t = a.currentTime + t0, o = a.createOscillator(), g = a.createGain();
  o.type = type || 'sine'; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
  if (vib){ const l = a.createOscillator(), lg = a.createGain(); l.frequency.value = vib[0]; lg.gain.value = vib[1]; l.connect(lg); lg.connect(o.frequency); l.start(t); l.stop(t + dur + .05); }
  g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(vol || .1, t + .02); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
  o.connect(g); g.connect(a.destination); o.start(t); o.stop(t + dur + .05);
}
function noise(t0, dur, o){
  // filtered white noise; o = {type, f0, f1, q, vol, attack}
  const a = AC, t = a.currentTime + t0, len = Math.ceil(a.sampleRate * dur), buf = a.createBuffer(1, len, a.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
  const src = a.createBufferSource(), f = a.createBiquadFilter(), g = a.createGain();
  src.buffer = buf; f.type = o.type || 'bandpass'; f.Q.value = o.q || 1;
  f.frequency.setValueAtTime(o.f0 || 1000, t); if (o.f1) f.frequency.exponentialRampToValueAtTime(o.f1, t + dur);
  const at = o.attack == null ? .01 : o.attack;
  g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(o.vol || .3, t + at); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
  src.connect(f); f.connect(g); g.connect(a.destination); src.start(t); src.stop(t + dur + .05);
}
const notes = (list, gap, dur, type, vol, t0 = 0) => list.forEach((f, i) => f && tone(f, t0 + i * gap, dur, type, vol));
// Recorded sound effects (sounds/, made with tools/sounds.py). sfx('file:<name>') plays one; if it can't load, the synth fallback plays.
const SOUND_FILES = {
  dragon: {src:'sounds/dragon.m4a', fallback:'roar'}, queue: {src:'sounds/queue.m4a', fallback:'queue'},
  castle: {src:'sounds/castle.m4a', fallback:'fanfare'}, poison: {src:'sounds/poison.m4a', fallback:'poison'},
  carriage: {src:'sounds/carriage.m4a', fallback:'gallop'}, unicorn: {src:'sounds/unicorn.m4a', fallback:'sparkle'},
  portal: {src:'sounds/portal.m4a', fallback:'portal'},
  splash: {src:'sounds/splash.m4a', fallback:'splash'}, boing: {src:'sounds/boing.m4a', fallback:'boing'},
  icecream: {src:'sounds/icecream.m4a', fallback:'jingle', stopOnClose:true}, juice: {src:'sounds/juice.m4a', fallback:'juice'},
  glide: {src:'sounds/glide.m4a', fallback:'glide'}, gust: {src:'sounds/gust.m4a', fallback:'gust'},
  cheer: {src:'sounds/cheer.m4a', fallback:'cheer'}
};
const soundBufs = {};
function loadSound(name){
  if (!soundBufs[name]) soundBufs[name] = fetch(SOUND_FILES[name].src).then(r => r.arrayBuffer())
    .then(b => new Promise((res, rej) => AC.decodeAudioData(b, res, rej))).catch(() => null);
  return soundBufs[name];
}
// Long sounds (stopOnClose) fade out when the card that is showing gets closed.
let cardSounds = [], cardSoundGen = 0;
function playFile(name){
  const long = SOUND_FILES[name].stopOnClose, gen = cardSoundGen;
  loadSound(name).then(buf => {
    if (long && gen !== cardSoundGen) return;          // the card was already closed while loading
    if (!buf){ sfx(SOUND_FILES[name].fallback); return; }
    const src = AC.createBufferSource(), g = AC.createGain(); g.gain.value = .9;
    src.buffer = buf; src.connect(g); g.connect(AC.destination); src.start();
    if (long) cardSounds.push({src, g});
  });
}
function fadeCardSounds(sec = .5){
  cardSoundGen++;
  if (!AC) return;
  const t = AC.currentTime;
  cardSounds.forEach(({src, g}) => { try { g.gain.setValueAtTime(g.gain.value, t); g.gain.linearRampToValueAtTime(0, t + sec); src.stop(t + sec + .05); } catch (e) {} });
  cardSounds = [];
}
function sfx(k){
  if (S.mute) return;
  if (k.startsWith('file:')){ if (ac()) playFile(k.slice(5)); return; }
  const a = ac(); if (!a) return;
  try {
    if (k === 'tick') tone(650 + Math.random() * 350, 0, .045, 'square', .035);
    else if (k === 'hop') tone(560, 0, .09, 'triangle', .07);
    else if (k === 'good') [523, 659, 784, 1047].forEach((f, i) => tone(f, i * .08, .2, 'triangle', .11));
    else if (k === 'magic') [784, 988, 1175, 1568, 1976].forEach((f, i) => tone(f, i * .07, .25, 'sine', .09));
    else if (k === 'bad') [440, 349].forEach((f, i) => tone(f, i * .15, .26, 'sine', .12));
    else if (k === 'win') [523, 659, 784, 659, 784, 1047].forEach((f, i) => tone(f, i * .12, .26, 'triangle', .13));
    else if (k === 'splash'){
      // a quick slip whistle, then a burst of filtered noise for the splash
      tone(900, 0, .18, 'sine', .07); tone(420, .1, .18, 'sine', .06);
      const len = a.sampleRate * .6, buf = a.createBuffer(1, len, a.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3);
      const src = a.createBufferSource(), bp = a.createBiquadFilter(), g = a.createGain();
      src.buffer = buf; bp.type = 'bandpass'; bp.frequency.setValueAtTime(1800, a.currentTime + .22); bp.frequency.exponentialRampToValueAtTime(350, a.currentTime + .8);
      g.gain.value = .5; src.connect(bp); bp.connect(g); g.connect(a.destination); src.start(a.currentTime + .22);
    }
    else if (k === 'flip'){         // 提示卡翻面: card swish + soft chime
      noise(0, .22, {f0:1500, f1:5000, q:1.2, vol:.18, attack:.04}); notes([1319, 1760], .08, .35, 'sine', .05, .18);
    }
    // ---- forest & castle ----
    else if (k === 'poison'){       // 毒蘑菇: three sick little bubbles, then a woozy slide down
      [0, .12, .24].forEach((t, i) => glide(300 + i * 60, 600 + i * 80, t, .09, 'sine', .08));
      glide(520, 140, .38, .75, 'triangle', .1, [7, 25]);
    }
    else if (k === 'snore'){        // 休息一轮: snore in, whistle out
      noise(0, .7, {type:'lowpass', f0:300, f1:500, q:3, vol:.45, attack:.3}); glide(160, 120, 0, .7, 'sawtooth', .05);
      glide(900, 1400, .85, .45, 'sine', .08);
    }
    else if (k === 'gallop'){       // 南瓜马车: clip-clop hooves, then a magic chime
      [0, .11, .3, .41, .6, .71].forEach((t, i) => { noise(t, .05, {f0: i % 2 ? 2600 : 1900, q:8, vol:.35, attack:.002}); tone(i % 2 ? 700 : 520, t, .05, 'square', .03); });
      notes([1047, 1319, 1568, 2093], .07, .3, 'sine', .07, .85);
    }
    else if (k === 'sparkle'){      // 独角兽: harp glissando up + shimmer
      notes([523, 659, 784, 988, 1175, 1319, 1568, 1976, 2349], .045, .35, 'triangle', .07);
      [0, .08, .16, .24].forEach(t => tone(2637 + Math.random() * 800, .45 + t, .2, 'sine', .04));
    }
    else if (k === 'portal'){       // 魔法门: rising whoosh through the door + chord
      noise(0, .9, {f0:300, f1:4000, q:2, vol:.25, attack:.4}); glide(220, 880, 0, .9, 'sine', .06, [6, 12]);
      notes([784, 988, 1175], 0, .6, 'sine', .06, .85);
    }
    else if (k === 'doorShut'){     // 魔法门没打开: creak, then a thump
      glide(180, 120, 0, .5, 'sawtooth', .03, [30, 20]); noise(.5, .25, {type:'lowpass', f0:220, q:1, vol:.6, attack:.003});
      tone(80, .5, .25, 'sine', .15);
    }
    else if (k === 'fanfare'){      // 到达城堡: trumpet fanfare + bells
      notes([523, 0, 523, 659, 784, 0, 659, 784], .11, .2, 'sawtooth', .08);
      notes([1047, 1319, 1568, 2093], .16, .8, 'sine', .06, .95);
    }
    // ---- animal-city sports day ----
    else if (k === 'jingle'){       // 冰淇淋车: music-box ice-cream truck tune
      notes([784, 659, 784, 1047, 988, 784, 880, 784, 659, 523], .14, .16, 'triangle', .09);
      notes([1568, 1319, 1568, 2093], .28, .12, 'sine', .03, .02);
    }
    else if (k === 'queue'){        // 还在排队: tick-tock waiting, then a sigh
      [0, .25, .5, .75].forEach((t, i) => noise(t, .04, {f0: i % 2 ? 1800 : 2600, q:6, vol:.5, attack:.002}));
      glide(600, 330, 1.0, .5, 'sine', .07);
    }
    else if (k === 'boing'){        // 蹦床: spring boing twice
      glide(150, 700, 0, .32, 'sine', .14, [18, 40]); glide(180, 900, .38, .38, 'sine', .12, [18, 50]);
    }
    else if (k === 'juice'){        // 能量果汁: slurp, then power-up arpeggio
      noise(0, .45, {f0:900, f1:2200, q:4, vol:.6, attack:.05}); glide(500, 900, 0, .4, 'triangle', .06, [25, 60]);
      notes([523, 659, 784, 1047, 1319, 1568], .05, .16, 'square', .06, .5);
    }
    else if (k === 'glide'){        // 滑翔伞起飞: wind swells up + a happy "wheee" whistle
      noise(0, 1.2, {f0:500, f1:1800, q:.8, vol:.2, attack:.5}); glide(700, 1800, .2, .9, 'sine', .07, [5, 30]);
    }
    else if (k === 'gust'){         // 风太大了: gust of wind blowing down
      noise(0, .9, {f0:1500, f1:300, q:.7, vol:.28, attack:.15}); glide(500, 200, .1, .7, 'sine', .04, [8, 20]);
    }
    else if (k === 'cheer'){        // 冲过终点: referee whistle, crowd cheer, fanfare
      [0, .12, .24].forEach(t => glide(2800, 2600, t, .1, 'sine', .08, [40, 120]));
      noise(.35, 1.6, {f0:1200, q:.5, vol:.25, attack:.35}); noise(.45, 1.4, {f0:2400, q:.8, vol:.12, attack:.3});
      notes([523, 659, 784, 1047], .12, .3, 'triangle', .1, .4);
    }
    else if (k === 'roar'){
      const len = a.sampleRate * .7, buf = a.createBuffer(1, len, a.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2) * (0.6 + 0.4 * Math.sin(i / 90));
      const src = a.createBufferSource(), lp = a.createBiquadFilter(), g = a.createGain();
      src.buffer = buf; lp.type = 'lowpass'; lp.frequency.value = 520; g.gain.value = .55;
      src.connect(lp); lp.connect(g); g.connect(a.destination); src.start();
      tone(110, 0, .6, 'sawtooth', .06);
    }
  } catch (e) {}
}
const canSpeak = 'speechSynthesis' in window && typeof SpeechSynthesisUtterance !== 'undefined';
// Recorded pronunciation (a little girl's voice, tools/voices.py) for the 300 built-in characters: sounds/zi/<code point>.m4a.
// Characters without a recording (e.g. from an uploaded list) fall back to the device's speech voice.
const hasVoice = ch => typeof HINTS !== 'undefined' && !!HINTS[ch];   // every built-in character (all 1000) has a girl-voice recording
const voiceBufs = {}; let voiceSrc = null;
function loadVoice(ch){
  if (!voiceBufs[ch]) voiceBufs[ch] = fetch(`sounds/zi/${ch.codePointAt(0).toString(16)}.m4a`).then(r => { if (!r.ok) throw 0; return r.arrayBuffer(); })
    .then(b => new Promise((res, rej) => AC.decodeAudioData(b, res, rej))).catch(() => null);
  return voiceBufs[ch];
}
function say(t){
  if (!t) return;
  if (hasVoice(t) && ac()){
    try { if (voiceSrc) voiceSrc.stop(); } catch (e) {}
    loadVoice(t).then(buf => {
      if (!buf){ speak(t); return; }
      const src = AC.createBufferSource(); src.buffer = buf; src.connect(AC.destination); src.start(); voiceSrc = src;
    });
    return;
  }
  speak(t);
}
function speak(t){
  if (!canSpeak || !t) return;
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(t);
    u.lang = 'zh-CN'; u.rate = .7;
    const vs = speechSynthesis.getVoices();
    const v = vs.find(v => /zh[-_]CN/i.test(v.lang)) || vs.find(v => /^zh/i.test(v.lang));
    if (v) u.voice = v;
    speechSynthesis.speak(u);
  } catch (e) {}
}

/* ---------- listening: the game hears the player read (Web Speech API; tested in lab/voice-test.html) ---------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const canListen = !!SR && window.isSecureContext;
let voiceBroken = false;   // voiceBroken: mic or recognition failed this session → parents judge instead
const useVoice = () => canListen && !voiceBroken && S.check !== 'parent';
const DIGITS = {'0':'零','1':'一','2':'二','3':'三','4':'四','5':'五','6':'六','7':'七','8':'八','9':'九','10':'十','100':'百','1000':'千','10000':'万'};
const noTone = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ü/g, 'v').toLowerCase();
// Sounds recognizers (and many grown-ups) mix up: zh/z, ch/c, sh/s, n/l, -ng/-n. A mix-up counts as "almost", not wrong.
const nearSound = s => noTone(s).replace(/^([zcs])h/, '$1').replace(/^l/, 'n').replace(/ng$/, 'n');
// Generous on purpose: any of the recognizer's guesses may match. Same character or a same-sounding character → 'ok';
// right syllable but another tone → 'half'; anything else → 'bad'.
function judgeReading(ch, py, P, alts){
  const heard = [];
  for (const a of alts){
    const cs = a.replace(/\d+/g, d => DIGITS[d] || d).match(/\p{Script=Han}/gu) || [];
    const pys = P && cs.length ? P.pinyin(cs.join(''), {type:'array'}) : [];
    cs.forEach((c, i) => heard.push({c, py: pys[i] || ''}));
  }
  if (heard.some(h => h.c === ch) || (py && heard.some(h => h.py === py))) return 'ok';
  if (py && heard.some(h => h.py && nearSound(h.py) === nearSound(py))) return 'half';
  return 'bad';
}
// Chrome decides by itself when the reader has stopped, and steady background noise (a fan, a fridge) keeps it waiting.
// So on Chrome/Edge we also watch the microphone level: once a voice was heard and it has been quiet for 0.6 s, stop
// (Chrome then gives its answer right away). Not on iPhone/iPad, where opening the mic twice can upset the audio, and
// not needed on Safari, which stops quickly by itself.
const useVAD = !/iPhone|iPad|iPod/.test(navigator.userAgent) && !(navigator.maxTouchPoints > 1 && /Macintosh/.test(navigator.userAgent))
  && /Chrome|Chromium|Edg\//.test(navigator.userAgent);
async function voiceWatch(onQuiet){
  let st, ctx, raf, stopped = false;
  try {
    st = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}});
    ctx = new (window.AudioContext || window.webkitAudioContext)(); await ctx.resume();
    const an = ctx.createAnalyser(); an.fftSize = 1024; ctx.createMediaStreamSource(st).connect(an);
    const buf = new Float32Array(an.fftSize), t0 = performance.now();
    let floor = 1, voiced = 0, quietSince = 0, last = t0;
    (function tick(){
      if (stopped) return;
      an.getFloatTimeDomainData(buf); let sum = 0; for (const v of buf) sum += v * v;
      const rms = Math.sqrt(sum / buf.length), now = performance.now(), dt = now - last; last = now;
      if (now - t0 < 300) floor = Math.min(floor, rms);                  // first 0.3 s: the room's own noise level
      else if (rms < floor * 1.5) floor = floor * 0.95 + rms * 0.05;     // then follow the room's noise slowly
      const loud = rms > Math.max(floor * 3, 0.012);
      if (loud){ voiced += dt; quietSince = 0; }
      else if (voiced > 120){ quietSince = quietSince || now; if (now - quietSince > 600){ onQuiet(); return; } }
      raf = requestAnimationFrame(tick);
    })();
  } catch (e) {}
  return () => { stopped = true; cancelAnimationFrame(raf); try { st && st.getTracks().forEach(t => t.stop()); } catch (e) {} try { ctx && ctx.close(); } catch (e) {} };
}
// Listen once for `ch`. Resolves {v, alts} or {err}. onStop receives a function that stops listening early.
async function listenFor(ch, onStop){
  const [P, d] = await Promise.all([loadPinyin().catch(() => null), hintData(ch)]);
  const py = d.py || '';
  return new Promise(res => {
    let rec, done = false, partial = [], stopT = null;
    let unwatch = null, spoke = false;
    const end = r => { if (done) return; done = true; clearTimeout(stopT); micBusy = false; if (unwatch) unwatch(); try { rec.abort(); } catch (e) {} res(r); };
    const stopSoon = ms => { clearTimeout(stopT); stopT = setTimeout(() => { try { rec.stop(); } catch (e) {} }, ms); };
    try {
      micBusy = true;
      try { if (navigator.audioSession) navigator.audioSession.type = 'auto'; } catch (e) {}
      rec = new SR(); rec.lang = 'zh-CN'; rec.interimResults = true; rec.continuous = false; rec.maxAlternatives = 5;
      rec.onstart = () => { stopSoon(6000);
        if (useVAD) voiceWatch(() => { spoke = true; try { rec.stop(); } catch (e) {} }).then(u => { if (done) u(); else unwatch = u; }); };
      rec.onresult = e => {
        const r = e.results[e.results.length - 1], alts = [...r].map(a => a.transcript.trim()).filter(Boolean);
        if (alts.length) partial = alts;
        // Safari often only sends "interim" guesses: accept as soon as one is right, otherwise stop 1.2 s after the last guess
        if (alts.length && (r.isFinal || judgeReading(ch, py, P, alts.slice(0, 1)) === 'ok')) end({v: judgeReading(ch, py, P, alts), alts});
        else stopSoon(1200);
      };
      rec.onerror = e => end(partial.length ? {v: judgeReading(ch, py, P, partial), alts: partial} : {err: e.error});
      rec.onend = () => end(partial.length ? {v: judgeReading(ch, py, P, partial), alts: partial} : {err: spoke ? 'unclear' : 'no-speech'});
      rec.start();
      onStop && onStop(() => { try { rec.stop(); } catch (e) {} }, () => end({err: 'aborted'}));
    } catch (e) { end({err: String(e && e.message || e)}); }
  });
}

/* ---------- modal & toast ---------- */
let lastAct = performance.now();
const touch = () => { lastAct = performance.now(); };
function settleScroll(max = 1200){
  return new Promise(res => {
    let last = window.scrollY, still = 0; const t0 = performance.now();
    (function tick(){
      const y = window.scrollY;
      still = Math.abs(y - last) < 0.5 ? still + 1 : 0; last = y;
      if (still >= 5 || performance.now() - t0 > max) return res();
      requestAnimationFrame(tick);
    })();
  });
}
async function card(o){
  if (o.zi && hasVoice(o.zi) && ac()) loadVoice(o.zi);   // start loading the pronunciation while the card opens
  await settleScroll();
  touch();
  return new Promise(res => {
    const ov = document.createElement('div');
    ov.className = 'overlay';
    const who = o.who ? `<div class="who"><span class="mini" style="--pc:${o.who.color}">${avHTML(o.who.avatar)}</span>${esc(nm(o.who))}</div>` : '';
    ov.innerHTML = `<div class="sheet" role="dialog" aria-modal="true">${who}
      ${o.img ? art(o.img, 'cardpic') : o.emo ? `<div class="big-emo">${o.emo}</div>` : ''}
      ${o.title ? `<h3>${esc(o.title)}</h3>` : ''}${o.html || ''}
      ${o.zi && o.hintP ? `<div class="flip" data-flip="1"><div class="flip-in"><div class="tzg face front"><span>${esc(o.zi)}</span></div><div class="face back"></div></div></div>`
        : o.learn ? learnHTML(o.zi, o.learn)
        : o.zi ? `<div class="tzg"><span>${esc(o.zi)}</span></div>` : ''}
      ${o.text ? `<p>${esc(o.text)}</p>` : ''}
      ${o.hintP ? `<button type="button" class="btn soft hintbtn" data-hint="1" ${o.hintP.hints !== 0 ? '' : 'disabled'}>${hintLabel(o.hintP)}</button>` : ''}
      ${o.listen ? `<div class="listen"><button type="button" class="mic" data-mic="1" aria-label="${L('点一下，然后读出来', 'Tap, then read it out loud')}">🎤</button>
        <div class="lmsg" aria-live="polite">${L('点 🎤，然后大声读出来', 'Tap 🎤, then read it out loud')}</div><div class="lheard"></div></div>
        <div class="row manual" hidden><button type="button" class="btn bad" data-k="no">${L('❌ 没读出来', '❌ Not yet')}</button><button type="button" class="btn good" data-k="yes">${L('✅ 读对了', '✅ Got it')}</button></div>` : ''}
      <div class="row">${o.btns.map(([k, l, c]) => `<button type="button" class="btn ${c || (o.btns.length === 1 ? 'primary' : '')} ${o.btns.length === 1 ? 'big' : ''}" data-k="${k}">${l}</button>`).join('')}</div>
      ${o.speak && (canSpeak || hasVoice(o.zi)) ? `<button type="button" class="link" data-say="1">🔊 ${L('听读音', 'Hear it')}</button>` : ''}</div>`;
    const shownAt = performance.now();
    let done = false;
    let stopMic = null, abortMic = null, tries = 0;
    const finish = k => { if (done) return; done = true; if (abortMic) abortMic(); touch(); fadeCardSounds(); ov.remove(); res(k); };
    const lmsg = (t, cls) => { const m = ov.querySelector('.lmsg'); if (m){ m.textContent = t; m.className = 'lmsg ' + (cls || ''); } };
    const heard = t => { const h = ov.querySelector('.lheard'); if (h) h.textContent = t ? L(`听到的是：${t}`, `I heard: ${t}`) : ''; };
    // Tap 🎤 → listen → right: done. Almost (tone or a similar sound): passes after playing the right sound. Wrong: one more try.
    async function onMic(){
      const btn = ov.querySelector('.mic');
      if (stopMic){ stopMic(); return; }
      touch(); btn.classList.add('on'); heard(''); lmsg(L('正在听……', 'Listening…'));
      const r = await listenFor(o.zi, (stop, abort) => { stopMic = stop; abortMic = abort; });
      stopMic = abortMic = null; btn.classList.remove('on');
      if (done) return;
      if (r.err){
        if (r.err === 'unclear'){ lmsg(L('听到声音了，但没听清是哪个字。靠近一点，再大声读一次', 'I heard you but couldn\'t make out the word — come closer and read it loudly again')); return; }
        if (r.err === 'no-speech' || r.err === 'aborted' || r.err === 'nomatch'){ lmsg(L('没听清，再点 🎤 读一次', 'Didn\'t catch that — tap 🎤 and try again')); return; }
        // microphone blocked or no recognition service: let a grown-up judge from now on
        voiceBroken = true; btn.disabled = true;
        lmsg(r.err === 'not-allowed' || r.err === 'service-not-allowed' ? L('不能用麦克风，请家长帮忙判断：', 'Can\'t use the microphone — a grown-up can judge instead:')
          : L('现在听不了（可能没连上网），请家长帮忙判断：', 'Can\'t listen right now (maybe no internet) — a grown-up can judge instead:'), 'bad');
        ov.querySelector('.manual').hidden = false; ov.querySelector('.listen + .manual + .row').hidden = true; return;
      }
      if (r.v === 'ok'){ btn.classList.add('ok'); lmsg(L('✅ 读对了！', '✅ You got it!'), 'ok'); await sleep(750); finish('yes'); return; }
      tries++; heard(r.alts[0]);
      if (r.v === 'half'){   // almost right (tone or a similar sound): passes, and the right pronunciation plays
        say(o.zi); lmsg(L('🟡 差不多，算你读对了！听听标准读音', '🟡 Close enough! Listen to how it sounds'), 'half'); await sleep(1900); finish('yes'); return;
      }
      if (tries >= 2){ lmsg(L('❌ 还是不太对', '❌ Not quite'), 'bad'); await sleep(900); finish('no'); return; }
      lmsg(L('❌ 好像不对，再读一次？', '❌ Hmm, not quite — try once more?'), 'bad');
    }
    const pick = e => {
      let b = e.target && e.target.closest ? e.target.closest('button') : null;
      if (!b && e.clientX != null){
        const x = e.clientX, y = e.clientY;
        b = [...ov.querySelectorAll('button')].find(bt => { const r = bt.getBoundingClientRect(); return x >= r.left - 6 && x <= r.right + 6 && y >= r.top - 6 && y <= r.bottom + 6; }) || null;
      }
      if (o.hintP && e.type === 'click' && (b ? b.dataset.hint : e.target.closest && e.target.closest('[data-flip]'))){ useHint(ov, o, !!(b && b.dataset.hint)); return; }
      if (!b || b.disabled) return;
      if (b.dataset.say){ if (e.type === 'click') say(o.zi); return; }
      if (b.dataset.mic){ if (e.type === 'click') onMic(); return; }
      if (!b.dataset.k || performance.now() - shownAt < 250) return;
      e.preventDefault();
      finish(b.dataset.k);
    };
    ov.addEventListener('click', pick);
    ov.addEventListener('pointerup', e => { if (e.pointerType === 'touch') pick(e); });
    document.body.appendChild(ov);
    const first = ov.querySelector('[data-k]'); if (first) first.focus({preventScroll:true});
    if (o.autoSay) setTimeout(() => say(o.zi), 300);
  });
}
/* ---------- hint cards: flip a character to see its pinyin and a common word ---------- */
const hintLabel = p => p.hints < 0 ? L('💡 提示', '💡 Hint') : p.hints > 0 ? L(`💡 提示（还剩 ${p.hints} 次）`, `💡 Hint (${p.hints} left)`) : L('💡 提示用完了', '💡 No hints left');
const hintDesc = n => n === 'inf' ? L('每人可以无限次使用提示', 'unlimited hints for everyone') : L(`每人有 ${n} 次提示`, `${n} hints per player`);
function loadPinyin(){
  return new Promise((res, rej) => {
    if (window.pinyinPro) return res(window.pinyinPro);
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/pinyin-pro@3.26.0/dist/index.js';
    s.onload = () => window.pinyinPro ? res(window.pinyinPro) : rej(new Error('no pinyinPro'));
    s.onerror = () => rej(new Error('load failed'));
    document.head.appendChild(s);
  });
}
async function hintData(ch){
  const mine = S.lib === 'mine' && S.mine.info && S.mine.info[ch];
  const base = typeof HINTS !== 'undefined' && HINTS[ch] ? { py: HINTS[ch][0], w: HINTS[ch][1], wpy: HINTS[ch][2] } : {};
  if (!mine && base.py) return base;
  const d = { py: mine && mine.py || base.py || '', w: mine && mine.w || base.w || '', wpy: mine && mine.w ? '' : base.wpy || '' };
  if (!d.py || (d.w && !d.wpy)){
    try {
      const P = await loadPinyin();
      if (!d.py) d.py = P.pinyin(ch);
      if (d.w && !d.wpy) d.wpy = P.pinyin(d.w);                  // whole word gives pinyin-pro context for polyphones
    } catch (e) {}
  }
  return d;
}
// Shown after a missed character: pinyin, the character and a common word, so it sticks next time (never costs a hint).
function hintBody(ch, d){
  const word = d.w ? esc(d.w).split(esc(ch)).join(`<b>${esc(ch)}</b>`) : '';
  return `<div class="py">${esc(d.py || '？')}</div>`
    + (d.w ? `<div class="ci">${word}</div><div class="cipy">${esc(d.wpy)}</div>` : `<div class="cipy">${d.py ? L('这个字还没有收录组词', 'No example word yet') : L('拼音加载不出来，请检查网络', 'Couldn\'t load pinyin — check the internet')}</div>`);
}
const learnHTML = (ch, d) => `<div class="learn"><div class="py">${esc(d.py || '')}</div><div class="lz">${esc(ch)}</div>${d.w ? `<div class="ci">${esc(d.w).split(esc(ch)).join(`<b>${esc(ch)}</b>`)}</div><div class="cipy">${esc(d.wpy || '')}</div>` : ''}</div>`;
// First tap spends one of the player's free hints and flips the card; after that the card flips back and forth for free.
async function useHint(ov, o, fromBtn){
  const flip = ov.querySelector('.flip'), btn = ov.querySelector('.hintbtn'), p = o.hintP;
  if (!flip || !btn) return;
  if (flip.dataset.shown){
    const on = flip.classList.toggle('on');
    btn.textContent = on ? L('🔄 翻回汉字', '🔄 Flip back') : L('💡 再看一下提示', '💡 See the hint again'); return;
  }
  if (!fromBtn || p.hints === 0 || flip.dataset.loading) return;
  flip.dataset.loading = '1'; cardHinted = true; if (p.hints > 0) p.hints--; saveG(); renderStatus(); sfx('flip');
  const d = await hintData(o.zi);
  flip.querySelector('.back').innerHTML = hintBody(o.zi, d);
  flip.dataset.shown = '1'; delete flip.dataset.loading;
  flip.classList.add('on'); btn.disabled = false; btn.textContent = L('🔄 翻回汉字', '🔄 Flip back');
}
async function toast(text, ms = 950){
  const t = document.createElement('div'); t.className = 'toast'; t.textContent = text;
  document.body.appendChild(t); await sleep(ms); t.remove();
}
function confetti(){
  if (RM) return;
  const cv = document.createElement('canvas'); cv.id = 'confetti'; document.body.appendChild(cv);
  const ctx = cv.getContext('2d'), dpr = window.devicePixelRatio || 1;
  const W = cv.width = innerWidth * dpr, H = cv.height = innerHeight * dpr;
  const cols = ['#E2475B','#FFC93E','#3FB873','#3B86E6','#9A68DE','#F6B3CF'];
  const ps = Array.from({length:150}, () => ({x: Math.random() * W, y: -Math.random() * H * .6, vx: (Math.random() - .5) * 3 * dpr, vy: (2 + Math.random() * 4) * dpr, s: (5 + Math.random() * 7) * dpr, r: Math.random() * 6, vr: (Math.random() - .5) * .3, c: cols[rnd(cols.length)]}));
  const t0 = performance.now();
  (function frame(t){
    ctx.clearRect(0, 0, W, H);
    ps.forEach(p => { p.x += p.vx; p.y += p.vy; p.r += p.vr; ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c; ctx.fillRect(-p.s / 2, -p.s / 3, p.s, p.s * .66); ctx.restore(); });
    if (t - t0 < 3200) requestAnimationFrame(frame); else cv.remove();
  })(t0);
}

/* ---------- setup screen ---------- */
const langBtn = () => `<button type="button" class="icon-btn lang" data-act="lang" aria-label="${L('Switch to English', '切换到中文')}">${L('EN', '中文')}</button>`;
function renderSetup(){
  const b = S.board, t = useTheme(b).t;
  const takenAv = S.players.map(p => p.avatar);
  const players = S.players.map((p, i) => `
    <div class="prow" style="--pc:${COLORS[i]}">
      <button type="button" class="avbtn" data-act="pickav" data-i="${i}" aria-label="${L('换头像', 'Change avatar')}">${avHTML(p.avatar)}</button>
      <div class="pcol"><input id="pname-${i}" data-i="${i}" maxlength="8" value="${esc(nm(p))}" aria-label="${L(`玩家${i + 1}的名字`, `Player ${i + 1} name`)}" autocomplete="off">
        ${(l => `<button type="button" class="who-chip ${p.noTrack ? 'off' : 'track'}" data-act="who" data-i="${i}" aria-expanded="${ui.openWho === i}">${p.noTrack ? L('👤 不记录进度', '👤 Not tracked') : L(`📈 记录${esc(l ? l.name : nm(p))}的进度`, `📈 Tracking ${esc(l ? l.name : nm(p))}`)} ▾</button>`)(learnerOf(p.learner))}</div>
      <button type="button" class="x" data-act="delp" data-i="${i}" aria-label="${L('去掉这个玩家', 'Remove this player')}" ${S.players.length <= 1 ? 'disabled' : ''}>✕</button>
    </div>
    ${ui.openWho === i ? `<div class="picker">
      <button type="button" data-act="setwho" data-i="${i}" data-v="" class="${p.noTrack ? 'on' : ''}">👤 ${L('不记录', 'Don\'t track')}<small>${L('家长、朋友，或者只是玩一玩', 'Grown-ups, friends, or just for fun')}</small></button>
      ${LP.list.map(l => { const taken = S.players.some((q, j) => j !== i && q.learner === l.id); return `<button type="button" data-act="setwho" data-i="${i}" data-v="${l.id}" class="${p.learner === l.id ? 'on' : ''}" ${taken ? 'disabled' : ''}>📈 ${esc(l.name)}<small>${taken ? L('已经在别的位置上', 'Already playing in another seat') : L(`已掌握 ${masteredCount(l.id)} 个字`, `${masteredCount(l.id)} characters mastered`)}</small></button>`; }).join('')}
      <button type="button" data-act="setwho" data-i="${i}" data-v="new">＋ ${L(`新学习者：${esc(nm(p))}`, `New learner: ${esc(nm(p))}`)}<small>${L('用这个名字开始记录进度（以后头像、名字随便换）', 'Start tracking under this name (avatar and name can change later)')}</small></button></div>` : ''}
    ${ui.openAv === i ? `<div class="avpick"><div class="avcre">${CREATURE_AVS.map(a => { const c = creatureOf(a); return `<button type="button" data-act="setav" data-i="${i}" data-av="${a}" class="${a === p.avatar ? 'on' : ''}" ${a !== p.avatar && takenAv.includes(a) ? 'disabled' : ''}>${avHTML(a)}<b>${EN() ? c.en : c.zh}</b><small>${EN() ? c.zh : c.en}</small></button>`; }).join('')}</div></div>` : ''}`).join('');
  const stepper = (k, label) => {
    const v = !b ? 0 : k === 'bridge' ? b.bridges.length : k === 'uni' ? b.cells.filter(c => c.uni).length : S.counts[k];
    return `<div class="step"><span class="nm">${label}</span><span class="ctl">
      <button type="button" data-act="dec" data-k="${k}" aria-label="${L('减少', 'Fewer')}">−</button><b>${v}</b>
      <button type="button" data-act="inc" data-k="${k}" aria-label="${L('增加', 'More')}">＋</button></span></div>`;
  };
  const mineN = (S.mine.chars || []).length;
  const hardN = (S.mine.hard || []).length;
  const libPanel = `
    <section class="panel"><h2>${L('选字库', 'Character list')}</h2>
      <div class="choices">
        <div role="button" tabindex="0" class="choice ${S.lib !== 'mine' ? 'on' : ''}" data-act="lib" data-v="${S.common}"><b>${L('常用字', 'Common characters')}</b><span class="libsel"><select id="libSize" aria-label="${L('常用字字库', 'Common characters list')}">
          ${COMMON.map(k => `<option value="${k}" ${S.common === k ? 'selected' : ''}>${L(`${k.slice(1)} 字`, `${k.slice(1)} characters`)}</option>`).join('')}</select></span>
          <span>${{c300: L('适合刚开始认字的小朋友', 'Great for kids just starting to read'), c500: L('认识一些字以后，再多学 200 个', 'Know a few already? 200 more to learn'),
            c1000: L('认字比较多的小朋友来挑战', 'A challenge for confident readers')}[S.common]}</span></div>
        <button type="button" class="choice ${S.lib === 'mine' ? 'on' : ''}" data-act="lib" data-v="mine"><b>${L('我的字库', 'My characters')}</b><span>${mineN ? `${L(`${mineN} 个字`, `${mineN} characters`)}${S.mine.name ? ' · ' + esc(S.mine.name) : ''}` : L('上传表格或粘贴汉字', 'Upload a spreadsheet or paste characters')}</span></button>
      </div>
      ${S.lib === 'mine' ? `
        <div class="row"><button type="button" class="btn soft" data-act="upload">📄 ${L('上传 Excel', 'Upload Excel')}</button><button type="button" class="btn soft" data-act="paste">✏️ ${L('粘贴汉字', 'Paste characters')}</button></div>
        <p class="note">${L(`点「上传 Excel」可以先下载表格模板：汉字一列必填，拼音和组词可以不填，难字写「难」会优先放${t.uni}。`, `Tap "Upload Excel" to get a template first: fill in the characters; pinyin and words are optional; mark tricky ones 「难」 to put the ${t.uni} there first.`)}${hardN ? L(`<br>已标出 ${hardN} 个难字。`, `<br>${hardN} tricky characters marked.`) : ''}</p>
        ${ui.pasting ? `<textarea id="pasteIn" aria-label="${L('粘贴汉字', 'Paste characters')}" placeholder="${L('把要练的汉字粘贴到这里', 'Paste the characters to practise here')}">${esc((S.mine.chars || []).join(''))}</textarea>
          <div class="row"><button type="button" class="btn" data-act="pastecancel">${L('取消', 'Cancel')}</button><button type="button" class="btn primary" data-act="pastesave">${L('保存字库', 'Save list')}</button></div>` : ''}` : ''}
      ${ui.libErr ? `<p class="err">${esc(ui.libErr)}</p>` : ''}${ui.libMsg ? `<p class="ok">${esc(ui.libMsg)}</p>` : ''}
      <div class="themes-h">${L('选主题', 'Choose a theme')}</div>
      <div class="themes">${LENS.map(n => { const o = BOARD_CHOICES[n]; return `<button type="button" data-act="len" data-v="${n}" class="theme ${S.len === n ? 'on' : ''}">
        <img src="${o.img}" alt="" draggable="false"><b>${EN() ? o.en : o.zh}</b>${(EN() ? o.subEn : o.subZh) ? `<i>${EN() ? o.subEn : o.subZh}</i>` : ''}<span>${L(`${n} 个字`, `${n} characters`)}</span></button>`; }).join('')}</div>
    </section>`;
  app.innerHTML = `
    <header class="top"><h1 class="logo">${L('识字蛇形棋', 'Hanzi Snakes & Ladders')}<small>${t.subtitle}</small></h1>
      <span class="topbtns"><button type="button" class="icon-btn" data-act="feedback" aria-label="${L('意见反馈', 'Feedback')}" title="${L('意见反馈', 'Feedback')}">💬</button>${langBtn()}<button type="button" class="icon-btn" data-act="mute" aria-label="${L('声音开关', 'Sound on/off')}">${S.mute ? '🔇' : '🔊'}</button></span></header>
    ${G && G.active ? `<button type="button" class="btn primary wide" data-act="resume">▶ ${L('继续上一局', 'Continue last game')}</button>` : ''}
    <section class="panel"><h2>${L('谁来玩？', 'Who\'s playing?')}</h2>
      <p class="note">${L('点头像可以换一个喜欢的人物。', 'Tap an avatar to pick your favourite creature.')}${L('<br>📈 会自动记录每个玩家认字的进度。家长或朋友可以点名字下面的标签，改成「不记录」。', '<br>📈 Each player\'s reading progress is tracked automatically. Grown-ups and friends can tap the label under their name and choose "Don\'t track".')}</p>
      ${players}
      ${S.players.length < 6 ? `<button type="button" class="btn soft" data-act="addp">＋ ${L('加一个玩家', 'Add a player')}</button>` : ''}
      ${LP.list.length ? `<button type="button" class="btn soft progbtn" data-act="progress">📈 ${L('学习进度', 'Progress')}<span>${LP.list.map(l => esc(l.name)).join(' · ')}</span></button>` : ''}
    </section>
    ${libPanel}
    <section class="panel"><h2>${L('棋盘', 'Board')}</h2>
      ${b ? `<p class="note">${L(`点任意一个汉字格，可以换字、放上或拿走${t.uni}，或者把${t.door}的${t.from}、${t.to}移过来。`, `Tap any character space to change the character, add or remove the ${t.uni}, or move a ${t.door} ${t.from} or ${t.to} there. `)}${t.toTop}</p>
      <div class="pbox" id="pbox">${mapHTML(b, {edit:true})}</div>
      <div class="steps">${stepper('dragon', art('dragon','ico') + ' ' + t.dragon)}${stepper('mush', art('mush','ico') + ' ' + t.mush)}${stepper('coach', art('coach','ico') + ' ' + t.coachS)}${stepper('bridge', art('portal','ico') + ' ' + t.door)}${stepper('uni', art('unicorn','ico') + ' ' + t.uni)}</div>
      <div class="row"><button type="button" class="btn soft" data-act="redraw">🎲 ${L('重新抽字', 'New characters')}</button><button type="button" class="btn soft" data-act="rearrange">🔀 ${L('道具换位置', 'Shuffle items')}</button></div>`
      : `<p class="err">${L('字库里至少要有 8 个字才能摆棋盘。', 'The list needs at least 8 characters to make a board.')}</p>`}
    </section>
    <section class="panel"><h2>${L('谁来听读得对不对？', 'Who checks the reading?')}</h2>
      <div class="seg wide">
        <button type="button" data-act="check" data-v="parent" class="${S.check === 'parent' || !canListen ? 'on' : ''}">👨‍👩‍👧 ${L('家长判断', 'A grown-up')}</button>
        <button type="button" data-act="check" data-v="voice" class="${S.check === 'voice' && canListen ? 'on' : ''}" ${canListen ? '' : 'disabled'}>🎤 ${L('游戏来听', 'The game listens')}</button></div>
      <p class="note">${!canListen ? L('这个浏览器不能自动听读音，由家长判断。想让游戏来听，请用 iPhone / iPad 的 Safari，或电脑上的 Chrome、Edge、Safari。', 'This browser can\'t listen, so a grown-up judges. For listening, use Safari on iPhone/iPad, or Chrome, Edge or Safari on a computer.')
        : S.check === 'voice' ? L('小朋友点 🎤 读出来，游戏会听读得对不对，一个人也能玩。单个字不容易听准，有时要多读一次。第一次会问能不能用麦克风，请点「允许」。声音只交给浏览器的语音识别（Apple 或 Google）听一下，我们不录音、不保存。', 'Kids tap 🎤 and read out loud; the game checks the reading, so they can play on their own. Single characters are hard to hear, so sometimes they\'ll need to read twice. The first time, allow the microphone. The voice only goes to the browser\'s speech recognition (Apple or Google); we don\'t record or keep it.')
        : L('读完后由家长点「读对了」或「没读出来」，卡片上可以听标准读音。小朋友一个人玩，或者家长不会中文时，可以选「🎤 游戏来听」。', 'After reading, a grown-up taps "Got it" or "Not yet" (the card can play the pronunciation). If the kid plays alone, or the grown-up doesn\'t read Chinese, choose "🎤 The game listens".')}</p>
    </section>
    <section class="panel"><h2>${L('提示卡', 'Hint cards')}</h2>
      <div class="lbl-row"><span>💡 ${L('用提示卡', 'Use hint cards')}</span><button type="button" class="switch ${S.hints ? 'on' : ''}" data-act="hints" role="switch" aria-checked="${S.hints}" aria-label="${L('提示卡开关', 'Hint cards on/off')}"><i></i></button></div>
      ${S.hints ? `<div class="lbl-row"><span>${L('每人可以用', 'Each player gets')}</span><div class="seg">${HINT_CHOICES.map(n => `<button type="button" data-act="hintn" data-v="${n}" class="${S.hintN === n ? 'on' : ''}">${n === 'inf' ? L('无限', 'Unlimited') : L(n + ' 次', String(n))}</button>`).join('')}</div></div>` : ''}
      <p class="note">${S.hints ? L('遇到不认识的字，可以用一次提示把卡片翻过来，看拼音和一个常用的词。中文好的小朋友可以关掉。', 'Stuck on a character? Use a hint to flip the card and see its pinyin and a common word. Strong readers can turn this off.') : L('提示卡关掉了，读字时没有提示。', 'Hint cards are off — no hints while reading.')}</p>
    </section>
    <button type="button" class="btn primary wide go" data-act="start" ${b ? '' : 'disabled'}>${L('开始游戏！', 'Start the game!')}</button>
    <section class="panel"><h2>${L('怎么玩', 'How to play')}</h2>
      <ul class="rules">
        <li><span>🎲</span><span>${t.ruleGoal}</span></li>
        <li><span>📖</span><span>${useVoice() ? L('走到汉字格，点 🎤 大声读出这个字，游戏会听你读得对不对。读错了可以再读一次，还是不对就回到上次的位置。', 'Land on a character? Tap 🎤 and read it out loud — the game listens. If it\'s not right you get one more try; otherwise go back to where you were.')
          : L('走到汉字格要大声读出这个字，读不出来就回到上次的位置。', 'Land on a character? Read it out loud! If you can\'t, go back to where you were.')}</span></li>
        <li><span>${art('dragon','ico')}</span><span>${t.ruleDragon}</span></li>
        <li><span>${art('mush','ico')}</span><span>${t.ruleMush}</span></li>
        <li><span>${art('coach','ico')}</span><span>${t.ruleCoach}</span></li>
        <li><span>${art('unicorn','ico')}</span><span>${t.ruleUni}</span></li>
        <li><span>${art('portal','ico')}</span><span>${t.ruleDoor}</span></li>
        ${S.hints ? `<li><span>💡</span><span>${L(`提示卡：${hintDesc(S.hintN)}，不认识的字可以翻开卡片看拼音和组词。`, `Hint cards: ${hintDesc(S.hintN)} — flip the card to see the pinyin and a word.`)}</span></li>` : ''}
      </ul>
    </section>
    <footer class="foot"><button type="button" class="link" data-act="feedback">💬 ${L('意见反馈', 'Send feedback')}</button>
      <p>${L('本网站只统计匿名的访问次数，不收集个人信息。', 'We only count anonymous visits — no personal information is collected.')}</p></footer>`;
}

/* ---------- progress page: one learner at a time ---------- */
function zStatus(id, ch){
  const r = LP.stats[id] && LP.stats[id].chars[ch];
  if (!r) return L('还没在棋盘上见过这个字。', 'Not seen on a board yet.');
  const n = L(`读对 ${r.ok + r.hint} 次（不用提示 ${r.ok} 次），没读出来 ${r.miss} 次。`, `Read right ${r.ok + r.hint}× (${r.ok}× without a hint), missed ${r.miss}×.`);
  const days = r.m ? Math.ceil(((r.due || 0) - Date.now()) / DAY) : 0;
  const next = !r.m ? '' : days <= 0 ? L('该复习了。', 'Due for review. ') : L(`${days} 天后复习。`, `Review in ${days} day${days === 1 ? '' : 's'}. `);
  if (r.f) return L('🏅 牢牢记住了！不用再复习。', '🏅 Fully learned — no more reviews needed. ') + n;
  return (r.m ? L('⭐ 已掌握，', '⭐ Mastered. ') + next : L(`正在学：不用提示再读对 ${Math.max(1, MASTER_OK - r.ok)} 次就掌握了。`, `Learning: ${Math.max(1, MASTER_OK - r.ok)} more right without a hint to master it. `)) + n;
}
function renderProgress(){
  const l = learnerOf(ui.progId) || LP.list[0];
  if (!l){ screen = 'setup'; renderSetup(); return; }
  ui.progId = l.id;
  const st = lstat(l.id);
  const lists = [['c300', L('300 字', '300')], ['c500', L('500 字', '500')], ['c1000', L('1000 字', '1000')]].concat((S.mine.chars || []).length ? [['mine', L('我的字库', 'My list')]] : []);
  const lib = lists.some(x => x[0] === ui.progLib) ? ui.progLib : (lists.some(x => x[0] === S.lib) ? S.lib : 'c300');
  const chars = lib === 'mine' ? S.mine.chars : commonChars(lib);
  const sm = listSummary(l.id, chars), all = Object.entries(st.chars), week = Date.now() - 7 * 864e5;
  const weekNew = all.filter(([, r]) => r.m > week).length, dueN = chars.filter(c => { const r = st.chars[c]; return r && r.m && !r.f && r.due <= Date.now(); }).length;
  const recent = all.filter(([, r]) => r.m).sort((a, b) => b[1].m - a[1].m).slice(0, 12).map(x => x[0]);
  const hard = all.filter(([, r]) => !r.m && r.miss).sort((a, b) => b[1].miss - a[1].miss).slice(0, 12);
  const C = 2 * Math.PI * 15.9, pct = sm.total ? sm.m / sm.total : 0;
  const cls = c => { const r = st.chars[c]; return r ? (r.f ? 'f' : r.m ? 'm' : 'l') : 'n'; };
  const zchip = c => `<button type="button" data-act="progz" data-v="${esc(c)}">${esc(c)}</button>`;
  app.innerHTML = `
    <header class="dash-top"><button type="button" class="icon-btn" data-act="progback" aria-label="${L('返回', 'Back')}">←</button>
      <span class="dav">${avHTML(l.avatar)}</span>
      <div class="dname"><b>${esc(l.name)}</b><small>${L(`玩了 ${st.games} 局 · 读了 ${st.reads} 次`, `${st.games} game${st.games === 1 ? '' : 's'} · ${st.reads} reading${st.reads === 1 ? '' : 's'}`)}</small></div>
      ${LP.list.length > 1 ? `<select id="progWho" aria-label="${L('换一个学习者', 'Switch learner')}">${LP.list.map(x => `<option value="${x.id}" ${x.id === l.id ? 'selected' : ''}>${esc(x.name)}</option>`).join('')}</select>` : ''}</header>
    <section class="panel"><div class="seg wide ptabs">${lists.map(([k, n]) => `<button type="button" data-act="proglib" data-v="${k}" class="${k === lib ? 'on' : ''}">${n}</button>`).join('')}</div>
      <div class="big">
        <svg class="ring" viewBox="0 0 36 36" role="img" aria-label="${L(`已掌握 ${sm.m} / ${sm.total}`, `${sm.m} of ${sm.total} mastered`)}"><circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--soft)" stroke-width="3.6"/>
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--leaf)" stroke-width="3.6" stroke-dasharray="${(C * pct).toFixed(2)} ${C.toFixed(2)}" stroke-linecap="round" transform="rotate(-90 18 18)"/>
          <text x="18" y="18" text-anchor="middle" font-size="8.5" fill="var(--ink)">${sm.m}</text><text x="18" y="24" text-anchor="middle" font-size="3.6" fill="var(--ink-soft)">/ ${sm.total}</text></svg>
        <div class="nums"><div><i class="dot m"></i>${L('已掌握', 'Mastered')} <b>${sm.m}</b></div><div><i class="dot l"></i>${L('正在学', 'Learning')} <b>${sm.l}</b></div>
          <div><i class="dot n"></i>${L('还没见过', 'Not seen yet')} <b>${sm.n}</b></div>${sm.f ? `<div><i class="dot f"></i>${L(`其中牢牢记住 <b>${sm.f}</b> 🏅`, `<b>${sm.f}</b> fully learned 🏅`)}</div>` : ''}${dueN ? `<div>🔁 ${L(`该复习 <b>${dueN}</b> 个`, `<b>${dueN}</b> due for review`)}</div>` : ''}${weekNew ? `<div>${L(`这周新学会 <b>${weekNew}</b> 个 🎉`, `<b>${weekNew}</b> new this week 🎉`)}</div>` : ''}</div>
      </div>
      <ul class="prules">
        <li><span>⭐</span><span>${L(`<b>掌握</b>：不用提示读对 ${MASTER_OK} 次。每局只算第一次读，这局已经有人读过的字不算。`, `<b>Mastered</b>: read right ${MASTER_OK} times without a hint. Only the first reading in a game counts — not after someone else read it out.`)}</span></li>
        <li><span>🔁</span><span>${L('<b>复习</b>：掌握后过 3 天、1 周、3 周、2 个月会再出现在棋盘上。', '<b>Review</b>: mastered characters come back after 3 days, 1 week, 3 weeks and 2 months.')}</span></li>
        <li><span>🏅</span><span>${L('<b>牢牢记住</b>：复习都读对，就不再出现。', '<b>Fully learned</b>: pass every review and it stops coming back.')}</span></li>
        <li><span>↩️</span><span>${L('<b>读错了</b>：回到「正在学」，重新开始。', '<b>Missed</b>: back to "learning" to start again.')}</span></li>
      </ul>
      ${recent.length ? `<h2>⭐ ${L('最近学会', 'Recently mastered')}</h2><div class="zchips">${recent.map(zchip).join('')}</div>` : ''}
    </section>
    <section class="panel"><h2>${L(`全部 ${chars.length} 个字`, `All ${chars.length} characters`)}</h2>
      <p class="note">${L('点一个字可以听读音、看组词和读过几次。', 'Tap a character to hear it, see a word and its history.')}</p>
      <div class="zgrid">${chars.map(c => `<button type="button" class="${cls(c)}" data-act="progz" data-v="${esc(c)}">${esc(c)}</button>`).join('')}</div>
    </section>
    ${hard.length ? `<section class="panel"><h2>💪 ${L('常读错，多练练', 'Often missed — keep practising')}</h2><div class="zchips">${hard.map(([c, r]) => `<button type="button" data-act="progz" data-v="${esc(c)}">${esc(c)}<small>${L(`错 ${r.miss} 次`, `${r.miss}× missed`)}</small></button>`).join('')}</div></section>` : ''}
    <footer class="foot"><p>${L('进度只保存在这台设备的这个浏览器里。', 'Progress is saved only in this browser on this device.')}</p>
      <div class="row"><button type="button" class="link" data-act="lrename">✏️ ${L('改名字', 'Rename')}</button><button type="button" class="link" data-act="ldelete">🗑️ ${L('删除这个学习者', 'Delete this learner')}</button></div></footer>`;
}

function rerenderSetupKeepScroll(){
  const y = window.scrollY, pb = document.getElementById('pbox'), py = pb ? pb.scrollTop : null;
  renderSetup(); window.scrollTo(0, y);
  const pb2 = document.getElementById('pbox');
  if (pb2) pb2.scrollTop = py == null ? pb2.scrollHeight : py;
}

/* tile editor (setup) */
// Magic doors in the tile sheet: each pair can have its entrance or exit moved to this tile (entrance must stay before exit).
function doorRows(i){
  const brs = S.board.bridges, t = TH.t; if (!brs.length) return '';
  const c = S.board.cells[i], here = brs.findIndex(l => l.from === i || l.to === i);
  const rows = brs.map((l, j) => {
    const mine = j === here;
    const okFrom = !mine && here < 0 && !c.uni && i < l.to, okTo = !mine && here < 0 && !c.uni && i > l.from;
    return `<div class="drow"><span class="dn" style="--dc:${DCOL[j % 5]}">${j + 1}</span>
      <button type="button" class="btn soft" data-t="from" data-j="${j}" ${okFrom ? '' : 'disabled'}>${art('portal','ico')} ${L(`${t.from}移到这里`, `Move ${t.from} here`)}</button>
      <button type="button" class="btn soft" data-t="to" data-j="${j}" ${okTo ? '' : 'disabled'}>${art('door','ico')} ${L(`${t.to}移到这里`, `Move ${t.to} here`)}</button></div>`;
  }).join('');
  const why = here >= 0 ? L(`这一格是 ${here + 1} 号${t.door}的${brs[here].from === i ? t.from : t.to}。`, `This space is the ${brs[here].from === i ? t.from : t.to} of ${t.door} ${here + 1}.`)
    : c.uni ? L(`这一格有${t.uni}，先拿走${t.uni}才能放${t.door}。`, `This space has the ${t.uni} — remove it first to place a ${t.door}.`) : L(`${t.from}要在${t.to}前面。`, `The ${t.from} must come before the ${t.to}.`);
  return `<div class="doors"><div class="dh">${t.door}</div>${rows}<p class="note">${why}</p></div>`;
}
function openTile(i){
  const ov = document.createElement('div'); ov.className = 'overlay';
  const paint = (msg, err) => {
    const c = S.board.cells[i], isBridge = bridgeEnds(S.board).has(i);
    ov.innerHTML = `<div class="sheet" role="dialog" aria-modal="true"><div class="who">${L(`第 ${i} 格`, `Space ${i}`)}</div>
      <div class="tzg"><span>${esc(c.ch)}</span></div>
      <button type="button" class="btn soft wide" data-t="rand">🎲 ${L('随机换一个字', 'Random character')}</button>
      <div class="inrow"><input id="ownCh" maxlength="4" placeholder="${L('自己输入', 'Type one')}" aria-label="${L('自己输入一个字', 'Type a character')}" autocomplete="off"><button type="button" class="btn soft" data-t="own">${L('换成这个字', 'Use it')}</button></div>
      <button type="button" class="btn soft wide" data-t="uni" ${isBridge ? 'disabled' : ''}>${art('unicorn','ico')} ${EN() ? `${c.uni ? 'Remove' : 'Add'} ${TH.t.uni}` : `${c.uni ? '拿走' : '放上'}${TH.t.uni}`}</button>
      ${isBridge ? `<p class="note">${L(`这一格有${TH.t.door}，不能放${TH.t.uni}。`, `This space has a ${TH.t.door}, so the ${TH.t.uni} can't go here.`)}</p>` : ''}
      ${doorRows(i)}
      ${msg ? `<p class="${err ? 'err' : 'ok'}">${esc(msg)}</p>` : ''}
      <button type="button" class="btn primary wide" data-t="done">${L('完成', 'Done')}</button></div>`;
  };
  ov.addEventListener('click', e => {
    const b = e.target.closest('[data-t]'); if (!b) return;
    const c = S.board.cells[i], t = b.dataset.t;
    if (t === 'done'){ ov.remove(); return; }
    if (t === 'rand'){
      const onBoard = new Set(boardChars(S.board));
      let pool = libChars().filter(ch => !onBoard.has(ch));
      if (!pool.length) pool = commonChars('c1000').filter(ch => !onBoard.has(ch));
      if (!pool.length){ paint(L('没有别的字可以换了。', 'There are no other characters to swap in.'), true); return; }
      c.ch = pool[rnd(pool.length)];
    } else if (t === 'own'){
      const v = hanOf(ov.querySelector('#ownCh').value)[0];
      if (!v){ paint(L('请输入一个汉字。', 'Please type a Chinese character.'), true); return; }
      if (v !== c.ch && boardChars(S.board).includes(v)){ paint(L(`「${v}」已经在棋盘上了。`, `「${v}」 is already on the board.`), true); return; }
      c.ch = v;
    } else if (t === 'uni'){
      c.uni = !c.uni;
    } else if (t === 'from' || t === 'to'){
      S.board.bridges[+b.dataset.j][t] = i;
    }
    saveS(); paint(); rerenderSetupKeepScroll();
  });
  paint();
  document.body.appendChild(ov);
}

/* library upload */
function loadXLSX(){
  return new Promise((res, rej) => {
    if (window.XLSX) return res(window.XLSX);
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
    s.onload = () => window.XLSX ? res(window.XLSX) : rej(new Error('no XLSX'));
    s.onerror = () => rej(new Error('load failed'));
    document.head.appendChild(s);
  });
}
// Columns are found by their header (汉字 / 拼音 / 组词 / 难字, or English); files without a recognised header
// keep the old layout: characters in column 1, "难" in column 2.
const COL_PATTERNS = { ch: /^(汉字|生字|字|字词|词语|词|characters?|chinese|hanzi)/i, py: /^(拼音|pinyin)/i,
  w: /^(组词|词组|例词|words?|example)/i, hard: /^(难|难字|hard|tricky)/i };
function rowsToLib(rows){
  const chars = [], hard = new Set(), info = {};
  const cell = (r, i) => i < 0 || r[i] == null ? '' : String(r[i]).replace(/^﻿/, '').trim();
  const head = (rows[0] || []).map((v, i) => cell(rows[0], i));
  const col = k => head.findIndex(h => COL_PATTERNS[k].test(h));
  const hasHead = col('ch') >= 0 || col('py') >= 0 || col('w') >= 0;
  const C = hasHead ? { ch: Math.max(0, col('ch')), py: col('py'), w: col('w'), hard: col('hard') } : { ch: 0, py: -1, w: -1, hard: 1 };
  rows.forEach((r, ri) => {
    if (hasHead && ri === 0) return;
    const cs = hanOf(cell(r, C.ch)); if (!cs.length) return;
    const h = /难|独角兽|果汁|hard|★|\*/i.test(cell(r, C.hard));
    const py = cell(r, C.py).replace(/\s+/g, ' '), w = hanOf(cell(r, C.w)).join('');
    cs.forEach(c => {
      chars.push(c); if (h) hard.add(c);
      const e = {};
      if (py && cs.length === 1) e.py = py;                       // pinyin only makes sense for a single character
      if (w && w.includes(c)) e.w = w; else if (!w && cs.length > 1) e.w = cs.join('');   // a word cell is its own example word
      if (Object.keys(e).length) info[c] = Object.assign(info[c] || {}, e);
    });
  });
  let u = uniq(chars);
  if (!u.length) u = uniq(rows.flatMap(r => r.flatMap(v => hanOf(v == null ? '' : v))));
  return { chars: u.slice(0, 1000), hard: [...hard].filter(c => u.includes(c)), info };
}
/* upload help: show the expected layout, offer a ready-made template, then pick the file */
// [character, pinyin, word, hard]
const TEMPLATE_ROWS = [['大', '', '', ''], ['小', '', '', ''], ['山', '', '', ''], ['熊', 'xióng', '熊猫', ''], ['乐', 'yuè', '音乐', ''],
  ['跳', '', '跳绳', '难'], ['朋友', '', '', ''], ['花', '', '', ''], ['鸟', '', '', '难'], ['鱼', '', '', '']];
const templateHead = () => [L('汉字', 'Characters'), L('拼音（可以不填）', 'Pinyin (optional)'), L('组词（可以不填）', 'Word (optional)'), L('难字（写「难」）', 'Hard? (write 难 or hard)')];
async function downloadTemplate(){
  const rows = [templateHead(), ...TEMPLATE_ROWS];
  const name = L('识字蛇形棋-字库模板', 'hanzi-character-list-template');
  let blob, file;
  try {
    const X = await loadXLSX(); const ws = X.utils.aoa_to_sheet(rows);
    ws['!cols'] = [{wch: 12}, {wch: 18}, {wch: 18}, {wch: 22}];
    const wb = X.utils.book_new(); X.utils.book_append_sheet(wb, ws, L('字库', 'Characters'));
    blob = new Blob([X.write(wb, {type:'array', bookType:'xlsx'})], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
    file = name + '.xlsx';
  } catch (e) {   // spreadsheet library didn't load: a CSV with BOM still opens in Excel
    blob = new Blob(['\uFEFF' + rows.map(r => r.join(',')).join('\r\n')], {type:'text/csv;charset=utf-8'}); file = name + '.csv';
  }
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = file; document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}
/* ---------- feedback (Tally form) & anonymous stats (GoatCounter) ---------- */
const FEEDBACK_URL = 'https://tally.so/r/PRjZ5x';   // Tally form link, e.g. https://tally.so/r/abc123 (the form has a hidden field "info")
const STATS_CODE = 'shizifun';     // GoatCounter site code: stats at https://<code>.goatcounter.com
const LOCAL = /^(127\.0\.0\.1|localhost|\[::1\])$/.test(location.hostname);   // local previews are never counted
if (STATS_CODE && !LOCAL){
  const sc = document.createElement('script'); sc.async = true; sc.src = 'https://gc.zgo.at/count.js';
  sc.dataset.goatcounter = `https://${STATS_CODE}.goatcounter.com/count`; document.head.appendChild(sc);
}
// Events show up in GoatCounter as paths like "start/c500/28"; no names or other personal data are sent.
function track(name){
  try { if (STATS_CODE && !LOCAL && window.goatcounter && window.goatcounter.count) window.goatcounter.count({path: name, title: name, event: true}); } catch (e) {}
}
const feedbackInfo = () => [S.lang, S.lib, S.len, /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent) ? 'phone' : 'computer', 'v53'].join(' · ');
function openFeedback(){
  track('feedback');
  const ov = document.createElement('div'); ov.className = 'overlay';
  ov.innerHTML = `<div class="sheet upl" role="dialog" aria-modal="true">
    <h3>💬 ${L('意见反馈', 'Feedback')}</h3>
    <p>${L('谢谢你玩识字蛇形棋！欢迎告诉我们：', 'Thanks for playing! We\'d love to hear:')}</p>
    <ul class="steps-l">
      <li>${L('喜欢什么，哪里不好玩，想要什么新功能', 'What you like, what\'s not fun, and what you\'d like added')}</li>
      <li>${L('遇到问题的话，可以附上截图或录屏', 'Found a problem? You can attach a screenshot or screen recording')}</li>
      <li>${L('想收到回复，可以留下联系方式（可以不填）', 'Leave a way to reach you if you\'d like a reply (optional)')}</li>
    </ul>
    <p class="note">${L('会在新页面打开一个反馈表，不用注册。', 'A feedback form opens in a new page — no sign-up needed.')}</p>
    <div class="row"><button type="button" class="btn soft" data-u="close">${L('取消', 'Cancel')}</button>
      <button type="button" class="btn primary" data-u="go" ${FEEDBACK_URL ? '' : 'disabled'}>✍️ ${L('去写反馈', 'Write feedback')}</button></div></div>`;
  ov.addEventListener('click', e => {
    const b = e.target.closest('[data-u]'); if (!b && e.target !== ov) return;
    if (b && b.dataset.u === 'go') window.open(`${FEEDBACK_URL}?info=${encodeURIComponent(feedbackInfo())}`, '_blank', 'noopener');
    ov.remove();
  });
  document.body.appendChild(ov);
}
function openUploadHelp(){
  // no board yet (empty list): pick the theme from the chosen length, about 8 item spaces on top of the characters
  const th = S.board ? themeOf(S.board) : THEMES[mapFor(S.len + 8).theme] || THEMES.forest, t = EN() ? th.en : th.t;
  const ov = document.createElement('div'); ov.className = 'overlay';
  const head = templateHead();
  ov.innerHTML = `<div class="sheet upl" role="dialog" aria-modal="true">
    <h3>${L('上传我的字库', 'Upload my characters')}</h3>
    <ol class="steps-l">
      <li>${L('先下载表格模板', 'Download the template')}</li>
      <li>${L('用 Excel、Numbers 或 WPS 打开，把要练的字填在「汉字」这一列（一格一个字或一个词）', 'Open it in Excel, Numbers or Google Sheets and put the characters in the "Characters" column (one character or word per cell)')}</li>
      <li>${L('「拼音」和「组词」可以不填：填了就显示在提示卡背面；不填会自动查拼音。多音字可以用拼音指定读音', '"Pinyin" and "Word" are optional: if filled, they show on the back of the hint card; if empty, pinyin is looked up automatically. Use pinyin to choose the reading of a character with several readings')}</li>
      <li>${L(`想让${t.uni}优先放在某个字上，就在「难字」这一列写「难」`, `To put the ${t.uni} on a tricky character first, write 难 or "hard" in the "Hard?" column`)}</li>
      <li>${L('保存后点「选择文件上传」', 'Save it, then tap "Choose file"')}</li>
    </ol>
    <table class="tpl"><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead>
      <tbody>${TEMPLATE_ROWS.slice(2, 7).map(([c, py, w, h]) => `<tr><td class="zi">${c}</td><td>${py}</td><td class="zi sm">${w}</td><td>${h}</td></tr>`).join('')}
      <tr><td colspan="4" class="more">……</td></tr></tbody></table>
    <p class="note">${L('至少要有 8 个字，最多 1000 个。也可以上传 CSV 文件。', 'At least 8 characters, up to 1000. CSV files work too.')}</p>
    <div class="row"><button type="button" class="btn soft" data-u="tpl">📥 ${L('下载模板', 'Download template')}</button>
      <button type="button" class="btn primary" data-u="pick">📤 ${L('选择文件上传', 'Choose file')}</button></div>
    <button type="button" class="link" data-u="close">${L('取消', 'Cancel')}</button></div>`;
  ov.addEventListener('click', e => {
    const b = e.target.closest('[data-u]'); if (!b) return;
    if (b.dataset.u === 'tpl') downloadTemplate();
    else if (b.dataset.u === 'pick'){ ov.remove(); document.getElementById('fileIn').click(); }
    else ov.remove();
  });
  document.body.appendChild(ov);
}
async function handleFile(file){
  ui.libErr = ''; ui.libMsg = L('正在读取……', 'Reading…'); rerenderSetupKeepScroll();
  try {
    let rows;
    if (/\.(csv|txt)$/i.test(file.name)){
      const text = (await file.text()).replace(/^\uFEFF/, '');
      rows = text.split(/\r?\n/).map(l => l.split(/[,\t，]/));
    } else {
      const X = await loadXLSX();
      const wb = X.read(await file.arrayBuffer(), {type:'array'});
      rows = X.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {header:1, defval:''});
    }
    const lib = rowsToLib(rows);
    if (lib.chars.length < 8){ ui.libMsg = ''; ui.libErr = L(`表格里只找到 ${lib.chars.length} 个汉字，至少要 8 个。请检查第一列。`, `Only found ${lib.chars.length} characters — need at least 8. Please check the first column.`); }
    else {
      S.mine = { chars: lib.chars, hard: lib.hard, info: lib.info, name: file.name.replace(/\.[^.]+$/, '') };
      S.lib = 'mine'; drawBoard(); saveS(); track('mylist/upload');
      ui.libMsg = L(`读到 ${lib.chars.length} 个字${lib.hard.length ? `，其中 ${lib.hard.length} 个难字` : ''}，棋盘已经重新抽好。`, `Read ${lib.chars.length} characters${lib.hard.length ? ` (${lib.hard.length} tricky)` : ''} — new board ready.`);
    }
  } catch (e) {
    ui.libMsg = ''; ui.libErr = L('这个文件读不出来。可以另存成 CSV 再试，或者直接用「粘贴汉字」。', 'Couldn\'t read this file. Try saving it as CSV, or use "Paste characters".');
  }
  rerenderSetupKeepScroll();
}
document.getElementById('fileIn').addEventListener('change', e => {
  const f = e.target.files && e.target.files[0]; e.target.value = '';
  if (f) handleFile(f);
});

/* ---------- game screen ---------- */
const FACES = {1:[4], 2:[0,8], 3:[0,4,8], 4:[0,2,6,8], 5:[0,2,4,6,8], 6:[0,2,3,5,6,8]};
const dieHTML = n => Array.from({length:9}, (_, i) => `<i class="${FACES[n].includes(i) ? 'on' : ''}"></i>`).join('');
const lastIdx = () => G.board.cells.length - 1;

function renderGame(){
  useTheme(G.board);
  app.innerHTML = `
    <div class="gbar" id="gbar">
      <div class="gtop"><button type="button" class="icon-btn" data-act="home" aria-label="${L('返回主页', 'Home')}">🏠</button>
        <div class="gwho" id="gwho"></div>
        <span class="topbtns">${langBtn()}<button type="button" class="icon-btn" data-act="mute" aria-label="${L('声音开关', 'Sound on/off')}">${S.mute ? '🔇' : '🔊'}</button></span></div>
      <div class="track"><span class="end">${art('start')}</span><div class="rail" id="rail"></div><span class="end">${art('end')}</span></div>
    </div>
    ${mapHTML(G.board, {game:true})}
    <div class="dock" id="dock"><div class="die" id="die" aria-hidden="true">${dieHTML(G.lastRoll || 1)}</div>
      <button type="button" class="btn primary roll" id="rollbtn" data-act="roll">🎲 ${L('掷骰子', 'Roll')}</button></div>`;
  renderStatus();
  requestAnimationFrame(() => scrollToCell(G.players[G.turn].pos, false, true));
}
function msgText(m){
  if (!m) return '';
  if (typeof m === 'string') return m;                       // games saved before the English version
  const p = G.players[m.i];
  if (m.k === 'roll') return L(`${nm(p)} 掷到了 ${m.n}`, `${nm(p)} rolled a ${m.n}`);
  if (m.k === 'win') return TH.t.winMsg(nm(p));
  if (m.k === 'oops') return L('刚才出了点小问题，请再掷一次', 'Oops — please roll again');
  return '';
}
function renderStatus(){
  const who = document.getElementById('gwho'); if (!who) return;
  const p = G.players[G.turn], last = lastIdx();
  who.innerHTML = `<div class="av" style="--pc:${p.color}">${avHTML(p.avatar)}</div><div><div class="nm">${L(`轮到 ${esc(nm(p))}`, `${esc(nm(p))}'s turn`)}${G.hintsOn ? `<span class="hl">💡${p.hints < 0 ? '∞' : p.hints}</span>` : ''}</div><div class="sub">${esc(msgText(G.msg) || L('点「掷骰子」往前走', 'Tap "Roll" to move'))}</div></div>`;
  document.getElementById('rail').innerHTML = G.players.map((q, i) => `<span class="dot ${i === G.turn ? 'now' : ''}" style="--pc:${q.color};left:${(Math.min(q.pos, last) / last * 100).toFixed(1)}%" title="${esc(nm(q))}">${q.skip ? '😴' : avHTML(q.avatar)}</span>`).join('');
  const rb = document.getElementById('rollbtn'); if (rb) rb.disabled = busy || G.winner != null;
  placeTokens();
}
function placeTokens(dur = 180){
  const wrap = document.getElementById('tokens'); if (!wrap) return;
  wrap.style.setProperty('--dur', dur + 'ms');
  if (wrap.children.length !== G.players.length){
    wrap.innerHTML = '';
    G.players.forEach(p => { const t = document.createElement('div'); t.className = 'token'; t.style.setProperty('--pc', p.color); t.innerHTML = `<i class="spot"></i><div class="face">${avHTML(p.avatar)}</div>`; wrap.appendChild(t); });
  }
  const g = geo(G.board.cells.length), last = lastIdx(), groups = {};
  G.players.forEach((p, i) => { const k = Math.min(p.pos, last); (groups[k] = groups[k] || []).push(i); });
  for (const [pos, ids] of Object.entries(groups)){
    const c = g.cells[+pos], m = ids.length;
    ids.forEach((pi, k) => {
      let dx, dy;
      // dx/dy = where the figure's feet stand, relative to the tile centre (map units; a tile is 58 wide)
      if (m === 1){ dx = 24; dy = 30; }
      else { const row = Math.floor(k / 3), per = Math.min(m - row * 3, 3); dx = (k % 3 - (per - 1) / 2) * 26 + row * 10; dy = 30 + row * 12; }
      const el = wrap.children[pi];
      el.style.left = ((c.x + dx) / MW * 100) + '%';
      el.style.top = ((c.y + dy) / g.H * 100) + '%';
      el.classList.toggle('now', pi === G.turn && G.winner == null);
    });
  }
}
function scrollToCell(idx, smooth = true, force = false){
  const map = document.getElementById('map'); if (!map) return;
  const g = geo(G.board.cells.length), mr = map.getBoundingClientRect();
  const y = mr.top + g.cells[Math.min(idx, g.cells.length - 1)].y / g.H * mr.height;
  const top = document.getElementById('gbar').getBoundingClientRect().bottom;
  const bot = document.getElementById('dock').getBoundingClientRect().top;
  if (!force && y > top + 80 && y < bot - 80) return;
  window.scrollBy({ top: y - (top + bot) / 2, behavior: smooth && !RM ? 'smooth' : 'auto' });
}
function hop(pi){
  const el = document.getElementById('tokens')?.children[pi]; if (!el) return;
  el.classList.remove('hop'); void el.offsetWidth; el.classList.add('hop');
}
async function stepTo(pi, target){
  const p = G.players[pi], dir = target > p.pos ? 1 : -1;
  while (p.pos !== target){ p.pos += dir; touch(); placeTokens(180); hop(pi); sfx('hop'); scrollToCell(p.pos); await sleep(240); }
  renderStatus();
}
async function jumpTo(pi, target, ms = 700){
  G.players[pi].pos = target; touch(); placeTokens(ms); scrollToCell(target, true, true); await sleep(ms + 120); renderStatus();
}
async function rollDie(){
  const die = document.getElementById('die');
  die.classList.add('shake');
  for (let i = 0; i < 9; i++){ die.innerHTML = dieHTML(1 + rnd(6)); sfx('tick'); await sleep(55); }
  const n = 1 + rnd(6);
  die.innerHTML = dieHTML(n); die.classList.remove('shake');
  await sleep(280);
  return n;
}

async function onRoll(){
  if (busy || !G || G.winner != null) return;
  busy = true; touch(); renderStatus();
  try { await turnFlow(); }
  catch (e) { busy = false; G.msg = {k:'oops'}; renderStatus(); }
}
setInterval(() => {
  if (screen !== 'game' || !busy || !G || G.winner != null) return;
  if (document.querySelector('.overlay')) { touch(); return; }
  if (performance.now() - lastAct > 9000){ busy = false; renderStatus(); }
}, 2000);
async function turnFlow(){
  const pi = G.turn, p = G.players[pi], last = lastIdx();
  scrollToCell(p.pos, true);
  const n = await rollDie();
  G.lastRoll = n; G.msg = {k:'roll', i:G.players.indexOf(p), n};
  renderStatus();
  p.prev = p.pos;
  await stepTo(pi, Math.min(p.pos + n, last));
  if (p.pos >= last) return win(pi);
  if (await resolve(pi)) return win(pi);
  await nextTurn();
}

async function resolve(pi){
  const p = G.players[pi], cell = G.board.cells[p.pos], last = lastIdx();
  if (cell.t === 'dragon'){
    sfx(TH.sfx.dragon); const mp = document.getElementById('map'); mp.classList.remove('boom'); void mp.offsetWidth; mp.classList.add('boom');
    const o = TH.t.dragonCard(nm(p));
    await card({who:p, img:'dragon', title:o.title, text:o.text, btns:[['ok',o.btn,'bad']]});
    await jumpTo(pi, 0, 900); return false;
  }
  if (cell.t === 'mush'){
    sfx(TH.sfx.mush);
    const o = TH.t.mushCard(nm(p));
    await card({who:p, img:'mush', title:o.title, text:o.text, btns:[['ok',o.btn]]});
    p.skip = true; return false;
  }
  if (cell.t === 'coach'){
    sfx(TH.sfx.coach);
    const o = TH.t.coachCard;
    await card({who:p, img:'coach', title:o.title, text:o.text, btns:[['ok',o.btn,'primary']]});
    await stepTo(pi, Math.min(p.pos + 2, last)); return p.pos >= last;
  }
  if (cell.t === 'char') return readFlow(pi, cell);
  return false;
}

// Tracked seats get their learner profile on their first reading (so seats that never play leave no empty profiles).
// A free learner with the same name is reused, so removing and re-adding "小明" doesn't make a second 小明.
function autoLearner(p){
  const name = (p.name || '').trim();
  const free = LP.list.find(l => l.name === name && !G.players.some(q => q !== p && q.learner === l.id));
  const l = free || newLearner(name, p.avatar);
  p.learner = l.id; lstat(l.id).games++; saveL();
  const sp = S.players[p.seat];
  if (sp && !sp.learner && !sp.noTrack && (sp.name || '').trim() === name){ sp.learner = l.id; saveS(); }
}
// Every reading of a learner is recorded; G.got[learner] collects this game's characters for the end-of-game summary.
let cardHinted = false;
async function readCard(p, ch, hint){
  cardHinted = false;
  // Only a character's first reading in a game can count toward mastery: after that everyone has heard it
  // (another player read it, or the "remember it" card played it), so a later right reading is recorded as helped.
  const seen = G.seen || (G.seen = []), heard = seen.includes(ch);
  const ok = await readCardRaw(p, ch, hint);
  if (!heard) seen.push(ch);
  if (!learnerOf(p.learner) && p.track) autoLearner(p);
  if (p.learner && learnerOf(p.learner)){
    const newly = recordRead(p.learner, ch, ok, cardHinted || heard);
    const got = G.got || (G.got = {}), e = got[p.learner] || (got[p.learner] = {ok: [], newM: []});
    if (ok && !e.ok.includes(ch)) e.ok.push(ch);
    if (newly && !e.newM.includes(ch)) e.newM.push(ch);
  }
  saveG();
  return ok;
}
function readCardRaw(p, ch, hint){
  // Listening mode: the game hears the reading, so there is no "hear it" button (it would give the answer away);
  // the pronunciation plays on the "remember it" card after a miss or after "I don't know".
  if (useVoice()) return card({who:p, zi:ch, text:hint, listen:true, hintP: G.hintsOn ? p : null, btns:[['no',L('🤔 我不会', '🤔 I don\'t know'),'soft']]}).then(k => k === 'yes');
  return card({who:p, zi:ch, text:hint, speak:true, hintP: G.hintsOn ? p : null, btns:[['no',L('❌ 没读出来', '❌ Not yet'),'bad'],['yes',L('✅ 读对了', '✅ Got it'),'good']]}).then(k => k === 'yes');
}
async function readFlow(pi, cell){
  const p = G.players[pi], last = lastIdx();
  const br = G.board.bridges.find(l => l.from === p.pos);
  let hint = L('大声读出这个字！', 'Read this character out loud!');
  if (cell.uni) hint = TH.t.uniHint;
  if (br) hint = TH.t.doorHint(G.board.bridges.indexOf(br) + 1);
  if (!(await readCard(p, cell.ch, hint))){
    sfx('bad');
    await card({who:p, title:L('没关系，记住它！', 'That\'s OK — remember it!'), zi:cell.ch, learn: await hintData(cell.ch), text:p.prev === 0 ? TH.t.backHome : L(`这次要回到第 ${p.prev} 格。`, `This time, go back to space ${p.prev}.`), speak:true, autoSay:true, btns:[['ok','Okay']]});
    await jumpTo(pi, p.prev, 600); return false;
  }
  sfx(cell.uni ? TH.sfx.uni : 'good');
  if (cell.uni){
    const o = TH.t.uniCard;
    await card({who:p, img:'unicorn', title:o.title, text:o.text, btns:[['ok',o.btn,'primary']]});
    await stepTo(pi, Math.min(p.pos + 3, last)); return p.pos >= last;
  }
  if (br){
    const top = G.board.cells[br.to];
    if (await readCard(p, top.ch, TH.t.doorHint2(G.board.bridges.indexOf(br) + 1, br.to))){
      sfx(TH.sfx.door);
      const o = TH.t.doorCard(nm(p), br.to);
      await card({who:p, img:'portal', title:o.title, text:o.text, btns:[['ok',o.btn,'primary']]});
      await jumpTo(pi, br.to, 900); return false;
    }
    sfx(TH.sfx.doorFail);
    await card({who:p, title:TH.t.doorFail.title, zi:top.ch, learn: await hintData(top.ch), text:TH.t.doorFail.text, speak:true, autoSay:true, btns:[['ok','Okay']]});
    scrollToCell(p.pos, true, true);
    return false;
  }
  await toast(L('读对啦！👏', 'Great reading! 👏'));
  return false;
}

async function nextTurn(){
  const n = G.players.length;
  G.turn = (G.turn + 1) % n; G.msg = '';
  for (let guard = 0; G.players[G.turn].skip && guard < n * 2; guard++){
    const q = G.players[G.turn];
    q.skip = false; renderStatus(); saveG(); scrollToCell(q.pos, true, true);
    const o = TH.t.skipCard(nm(q));
    sfx(TH.sfx.skip);
    await card({who:q, img:'mush', title:o.title, text:o.text, btns:[['ok',o.btn]]});
    G.turn = (G.turn + 1) % n;
  }
  busy = false; saveG(); renderStatus();
  scrollToCell(G.players[G.turn].pos, true, true);
}

// After a game: one card for everyone tracked — what each read right, and which characters are newly mastered.
function summaryCard(rows){
  const chars = libChars();
  const html = `<div class="sums">${rows.map(([l, e]) => { const sm = listSummary(l.id, chars); return `<div class="sumrow">
    <div class="sumwho"><span class="mini">${avHTML(l.avatar)}</span><b>${esc(l.name)}</b><span>${e.ok.length ? L(`读对 ${e.ok.length} 个字`, `${e.ok.length} read right`) : L('下次加油！', 'Next time!')}</span></div>
    ${e.ok.length ? `<div class="sumz">${e.ok.slice(0, 12).map(c => `<span class="${e.newM.includes(c) ? 'new' : ''}">${esc(c)}</span>`).join('')}</div>` : ''}
    <p class="sumtxt">${e.newM.length ? L(`⭐ 新掌握 ${e.newM.length} 个：${e.newM.join('、')}。`, `⭐ ${e.newM.length} newly mastered: ${e.newM.join(' ')}. `) : ''}${L(`已掌握 ${sm.m} / ${sm.total}`, `Mastered ${sm.m} / ${sm.total}`)}</p></div>`; }).join('')}</div>`;
  return card({title: L('这局学到了什么', 'This game\'s reading'), html, btns: [['prog', L('📈 看进度', '📈 Progress'), 'soft'], ['ok', 'Okay', 'primary']]});
}
async function win(pi){
  const p = G.players[pi];
  p.pos = lastIdx();
  G.winner = pi; G.active = false; G.msg = {k:'win', i:pi};
  saveG(); renderStatus(); scrollToCell(p.pos, true, true); sfx(TH.sfx.win); confetti();
  const wc = TH.t.winCard(nm(p));
  const k = await card({who:p, img:'win', title:wc.title, text:wc.text, btns:[['setup',L('🏠 返回主页', '🏠 Home'),'home big'],['again',L('🎲 再玩一局', '🎲 Play again'),'primary big']]});
  busy = false;
  drawBoard(); saveS();  // every new game gets fresh characters and freshly placed props, unicorns and doors
  const rows = Object.entries(G.got || {}).map(([id, e]) => [learnerOf(id), e]).filter(([l]) => l);
  if (rows.length && await summaryCard(rows) === 'prog'){ screen = 'progress'; ui.progId = rows[0][0].id; render(); window.scrollTo(0, 0); return; }
  track(k === 'again' ? 'win/again' : 'win/home');
  if (k === 'again' && S.board) newGame(S.players, S.board);
  else { screen = 'setup'; render(); window.scrollTo(0, 0); }
}

function newGame(players, board){
  players.forEach(p => { if (learnerOf(p.learner)) lstat(p.learner).games++; }); saveL();
  G = { players: players.map((p, i) => ({name: (p.name || '').trim() || L(`玩家${i + 1}`, `Player ${i + 1}`), avatar: p.avatar, learner: learnerOf(p.learner) ? p.learner : null, track: !p.noTrack, seat: i, color: COLORS[i], pos:0, prev:0, skip:false, hints: !S.hints ? 0 : S.hintN === 'inf' ? -1 : S.hintN})),
        board: JSON.parse(JSON.stringify(board)), hintsOn: !!S.hints, turn:0, winner:null, active:true, lastRoll:1, msg:'' };
  busy = false; saveG(); screen = 'game'; render();
  try { if (navigator.wakeLock) navigator.wakeLock.request('screen').catch(() => {}); } catch (e) {}
}

/* ---------- events ---------- */
document.addEventListener('click', e => {
  if (e.target.closest('select')) return;   // the dropdown handles itself (re-rendering would close it)
  const b = e.target.closest('[data-act]'); if (!b || !app.contains(b)) return;
  const act = b.dataset.act, i = +b.dataset.i;
  ac();
  switch (act){
    case 'lang': S.lang = EN() ? 'zh' : 'en'; track(`lang/${S.lang}`); saveS(); document.documentElement.lang = EN() ? 'en' : 'zh-CN'; render(); return;
    case 'mute': S.mute = !S.mute; saveS(); b.textContent = S.mute ? '🔇' : '🔊'; return;
    case 'roll': onRoll(); return;
    case 'home': if (busy) return; screen = 'setup'; render(); window.scrollTo(0, 0); return;
    case 'resume': screen = 'game'; render(); return;
    case 'start': if (S.board){ track(`start/${S.lib}/${S.len}`); newGame(S.players, S.board); } return;
    case 'tile': openTile(i); return;
    case 'upload': openUploadHelp(); return;
    case 'feedback': openFeedback(); return;
    case 'pickav': ui.openAv = ui.openAv === i ? -1 : i; ui.openWho = -1; break;
    case 'who': ui.openWho = ui.openWho === i ? -1 : i; ui.openAv = -1; break;
    case 'setwho': {
      const v = b.dataset.v, pl = S.players[i];
      if (v === 'new'){ pl.learner = newLearner(nm(pl), pl.avatar).id; pl.noTrack = false; }
      else if (!v){ pl.learner = null; pl.noTrack = true; }   // grown-ups, friends: remembered for this seat
      else if (learnerOf(v) && !S.players.some((q, j) => j !== i && q.learner === v)){ pl.learner = v; pl.noTrack = false; }
      ui.openWho = -1; drawBoard(); break;   // a new board that suits who is playing
    }
    case 'progress': ui.progId = (learnerOf(ui.progId) || learnerOf((S.players.find(p => learnerOf(p.learner)) || {}).learner) || LP.list[0] || {}).id || null;
      screen = 'progress'; render(); window.scrollTo(0, 0); return;
    case 'progback': screen = 'setup'; render(); window.scrollTo(0, 0); return;
    case 'proglib': ui.progLib = b.dataset.v; renderProgress(); return;
    case 'progz': { const ch = b.dataset.v; (async () => card({zi: ch, learn: await hintData(ch), text: zStatus(ui.progId, ch), speak: true, autoSay: true, btns: [['ok', 'Okay']]}))(); return; }
    case 'lrename': {
      const l = learnerOf(ui.progId); if (!l) return;
      const v = (prompt(L('新名字：', 'New name:'), l.name) || '').trim().slice(0, 8);
      if (v){ l.name = v; saveL(); } renderProgress(); return;
    }
    case 'ldelete': {
      const l = learnerOf(ui.progId); if (!l) return;
      if (!confirm(L(`删除「${l.name}」和 TA 的全部学习进度？删除后不能恢复。`, `Delete "${l.name}" and all of their progress? This can't be undone.`))) return;
      LP.list = LP.list.filter(x => x.id !== l.id); delete LP.stats[l.id]; saveL();
      S.players.forEach(p => { if (p.learner === l.id) p.learner = null; }); saveS();
      ui.progId = (LP.list[0] || {}).id || null; screen = LP.list.length ? 'progress' : 'setup'; render(); window.scrollTo(0, 0); return;
    }
    case 'setav': {
      // picking a creature also names the player after it, unless the player already typed their own name
      const pl = S.players[i], prev = creatureOf(pl.avatar), next = creatureOf(b.dataset.av);
      if (next && (/^玩家\d+$/.test(pl.name) || (prev && pl.name === prev.zh) || !pl.name.trim())) pl.name = next.zh;
      pl.avatar = b.dataset.av; ui.openAv = -1; break;
    }
    case 'addp': {
      if (S.players.length >= 6) return;
      const used = S.players.map(p => p.avatar);
      const av = CREATURE_AVS.find(a => !used.includes(a));
      S.players.push({name: creatureOf(av) ? creatureOf(av).zh : `玩家${S.players.length + 1}`, avatar: av}); ui.openAv = -1; break;
    }
    case 'delp': if (S.players.length > 1){ S.players.splice(i, 1); ui.openAv = -1; } break;
    case 'lib': {
      const v = b.dataset.v; ui.libErr = ''; ui.libMsg = '';
      if (S.lib === v) return;
      S.lib = v; ui.pasting = v === 'mine' && !(S.mine.chars || []).length ? false : ui.pasting;
      drawBoard(); break;
    }
    case 'hints': S.hints = !S.hints; break;
    case 'check': S.check = b.dataset.v === 'parent' ? 'parent' : 'voice'; voiceBroken = false; break;
    case 'hintn': S.hintN = b.dataset.v === 'inf' ? 'inf' : +b.dataset.v; break;
    case 'len': S.len = +b.dataset.v; S.counts = defaultCounts(S.len); drawBoard(); break;
    case 'paste': ui.pasting = !ui.pasting; ui.libErr = ''; ui.libMsg = ''; break;
    case 'pastecancel': ui.pasting = false; break;
    case 'pastesave': {
      const list = uniq(hanOf(document.getElementById('pasteIn').value));
      if (list.length < 8){ ui.libErr = L(`现在只有 ${list.length} 个汉字，至少要 8 个。`, `Only ${list.length} characters — need at least 8.`); ui.libMsg = ''; break; }
      S.mine = { chars: list.slice(0, 1000), hard: [], name: '' }; S.lib = 'mine'; ui.pasting = false; ui.libErr = '';
      ui.libMsg = L(`保存了 ${Math.min(list.length, 1000)} 个字，棋盘已经重新抽好。`, `Saved ${Math.min(list.length, 1000)} characters — new board ready.`); drawBoard(); break;
    }
    case 'redraw': drawBoard(); break;
    case 'rearrange': rearrange(); break;
    case 'inc': case 'dec': {
      if (!S.board) return;
      const k = b.dataset.k, [lo, hi] = LIMITS[k], d = act === 'inc' ? 1 : -1;
      if (k === 'uni'){
        const ends = bridgeEnds(S.board), cells = S.board.cells;
        if (d > 0){
          const pref = new Set(S.lib === 'mine' ? S.mine.hard || [] : []);
          const cand = cells.map((c, j) => j).filter(j => cells[j].t === 'char' && !cells[j].uni && !ends.has(j));
          if (!cand.length || cells.filter(c => c.uni).length >= hi) return;
          const hard = cand.filter(j => pref.has(cells[j].ch)), pool = hard.length ? hard : cand;
          cells[pool[rnd(pool.length)]].uni = true;
        } else {
          const on = cells.map((c, j) => j).filter(j => cells[j].uni);
          if (!on.length) return;
          cells[on[rnd(on.length)]].uni = false;
        }
        S.counts.uni = cells.filter(c => c.uni).length; break;
      }
      const cur = k === 'bridge' ? S.board.bridges.length : S.counts[k];
      const next = Math.max(lo, Math.min(hi, cur + d));
      if (next === cur) return;
      S.counts[k] = next; S.counts.uni = S.board.cells.filter(c => c.uni).length; rearrange(); break;
    }
    default: return;
  }
  saveS(); rerenderSetupKeepScroll();
});
document.addEventListener('change', e => {
  if (e.target.id === 'progWho'){ ui.progId = e.target.value; renderProgress(); return; }
  if (e.target.id !== 'libSize') return;
  S.common = S.lib = e.target.value; ui.libErr = ''; ui.libMsg = ''; drawBoard(); saveS(); rerenderSetupKeepScroll();
});
document.addEventListener('keydown', e => {   // the common-list card is a div (it holds a <select>), so make Enter/Space work
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('div.choice[data-act]')){ e.preventDefault(); e.target.click(); }
});
document.addEventListener('input', e => {
  const t = e.target;
  if (t.id && t.id.startsWith('pname-')){ S.players[+t.dataset.i].name = t.value; saveS(); }
});

function render(){
  if (screen === 'game' && G) renderGame();
  else if (screen === 'progress' && LP.list.length) renderProgress();
  else { screen = 'setup'; renderSetup(); const pb = document.getElementById('pbox'); if (pb) pb.scrollTop = pb.scrollHeight; }
}
render();
})();
