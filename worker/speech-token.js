// Cloudflare Worker for 识字蛇形棋 (https://jinhy1007.github.io/Hanzi-Snake-Ladder/).
//
//   GET  /                 a short-lived (10-minute) Azure Speech token, so the Azure key never reaches the browser
//   POST /sync/new         store a family's learner progress, get a new family sync code back
//   GET  /sync/<code>      read it
//   PUT  /sync/<code>?base=<updated>   replace it (only if nobody else saved since <updated>; otherwise 409)
//   (too many requests from one IP → 429, see LIMITS)
//
// Setup (Cloudflare dashboard → Workers & Pages → this Worker → Settings):
//   Variables and Secrets:  AZURE_KEY (Secret) = KEY 1 of the Azure Speech resource; AZURE_REGION (Text) = e.g. westus2
//   Bindings:               D1 database, variable name DB → the "hanzi-sync" database (the table is created automatically)
//
// The sync code is the only key to a family's data: nicknames and per-character reading counts, nothing personal.
//
// Rate limits: the Origin check only stops other websites in a browser; a script can send any Origin. So each IP may
// only make so many requests per window, and some actions also have a daily cap for everyone together (counted in the
// same D1 database, table "hits"). Over the limit → 429. The game then falls back (browser speech, or syncs later).
const ALLOWED = ['https://jinhy1007.github.io', 'http://127.0.0.1:8765', 'http://localhost:8765'];
const CODE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';   // no 0/O, 1/I/L: easy to read out and type
const MAX_BYTES = 400000;
//          [per IP, window in seconds, daily cap for everyone (0 = none)]
const LIMITS = {
  token: [20, 600, 3000],     // the game keeps a token for 8 minutes, so a player needs only a few an hour
  create: [5, 3600, 300],     // new family sync codes
  sync: [300, 600, 0],        // reading and saving progress (a game syncs a few times a minute while playing)
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get('Origin') || '';
    const ok = ALLOWED.includes(origin);
    const cors = { 'Access-Control-Allow-Origin': ok ? origin : ALLOWED[0], 'Vary': 'Origin', 'Cache-Control': 'no-store' };
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: { ...cors, 'Access-Control-Allow-Methods': 'GET, POST, PUT', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '86400' } });
    }
    if (!ok) return new Response('Forbidden', { status: 403, headers: cors });
    try {
      const isSync = url.pathname.startsWith('/sync');
      const kind = !isSync ? 'token' : request.method === 'POST' ? 'create' : 'sync';
      if (await overLimit(env, kind, request.headers.get('CF-Connecting-IP') || 'unknown')) {
        return json({ error: 'too many requests' }, 429, { ...cors, 'Retry-After': '600' });
      }
      if (isSync) return await sync(request, env, url, cors);
      return await speechToken(env, cors);
    } catch (e) {
      console.log('error', e && e.stack || e);
      return json({ error: 'server error' }, 500, cors);
    }
  },
};

// Counts this request; true if the IP (or everyone, for the daily cap) is over the limit.
async function overLimit(env, kind, ip) {
  if (!env.DB) return false;
  const [perIp, win, daily] = LIMITS[kind], now = Date.now(), sec = Math.floor(now / 1000);
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS hits (k TEXT PRIMARY KEY, n INTEGER NOT NULL, exp INTEGER NOT NULL)').run();
  if (Math.random() < 0.01) await env.DB.prepare('DELETE FROM hits WHERE exp < ?').bind(now).run();
  const bump = (k, exp) => env.DB.prepare('INSERT INTO hits (k, n, exp) VALUES (?, 1, ?) ON CONFLICT(k) DO UPDATE SET n = n + 1 RETURNING n')
    .bind(k, exp).first('n');
  const bucket = Math.floor(sec / win);
  if (await bump(`${kind}:${ip}:${bucket}`, (bucket + 1) * win * 1000) > perIp) return true;
  if (!daily) return false;
  const day = Math.floor(sec / 86400);
  return await bump(`${kind}:all:${day}`, (day + 1) * 86400000) > daily;
}

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), { status, headers: { ...cors, 'Content-Type': 'application/json' } });
}

async function speechToken(env, cors) {
  if (!env.AZURE_KEY || !env.AZURE_REGION) return new Response('Worker is missing AZURE_KEY or AZURE_REGION', { status: 500, headers: cors });
  const r = await fetch(`https://${env.AZURE_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken`, {
    method: 'POST',
    headers: { 'Ocp-Apim-Subscription-Key': env.AZURE_KEY },
  });
  if (!r.ok) return new Response(`Azure said ${r.status}`, { status: 502, headers: cors });
  return json({ token: await r.text(), region: env.AZURE_REGION }, 200, cors);
}

function newCode() {
  const b = crypto.getRandomValues(new Uint8Array(12));
  return Array.from(b, x => CODE_CHARS[x % CODE_CHARS.length]).join('');
}

async function sync(request, env, url, cors) {
  if (!env.DB) return json({ error: 'Worker has no D1 binding named DB' }, 500, cors);
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS families (code TEXT PRIMARY KEY, data TEXT NOT NULL, updated INTEGER NOT NULL, created INTEGER NOT NULL)').run();
  const part = url.pathname.split('/')[2] || '';
  const body = request.method === 'GET' ? '' : await request.text();
  if (body.length > MAX_BYTES) return json({ error: 'too big' }, 413, cors);
  if (body) { try { JSON.parse(body); } catch (e) { return json({ error: 'not JSON' }, 400, cors); } }
  const now = Date.now();

  if (request.method === 'POST' && part === 'new') {
    if (!body) return json({ error: 'empty' }, 400, cors);
    for (let i = 0; i < 5; i++) {
      const code = newCode();
      const r = await env.DB.prepare('INSERT OR IGNORE INTO families (code, data, updated, created) VALUES (?, ?, ?, ?)').bind(code, body, now, now).run();
      if (r.meta && r.meta.changes) return json({ code, updated: now }, 200, cors);
    }
    return json({ error: 'could not make a code' }, 500, cors);
  }

  const code = part.toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (code.length !== 12) return json({ error: 'bad code' }, 400, cors);
  const row = await env.DB.prepare('SELECT data, updated FROM families WHERE code = ?').bind(code).first();
  if (!row) return json({ error: 'not found' }, 404, cors);

  if (request.method === 'GET') return json({ data: JSON.parse(row.data), updated: row.updated }, 200, cors);

  if (request.method === 'PUT') {
    if (!body) return json({ error: 'empty' }, 400, cors);
    const base = Number(url.searchParams.get('base'));
    if (base !== row.updated) return json({ error: 'changed', updated: row.updated }, 409, cors);
    const next = Math.max(now, row.updated + 1);
    const r = await env.DB.prepare('UPDATE families SET data = ?, updated = ? WHERE code = ? AND updated = ?').bind(body, next, code, row.updated).run();
    if (!r.meta || !r.meta.changes) return json({ error: 'changed' }, 409, cors);
    return json({ updated: next }, 200, cors);
  }
  return json({ error: 'method' }, 405, cors);
}
