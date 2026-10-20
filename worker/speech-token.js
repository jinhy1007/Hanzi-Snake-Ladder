// Cloudflare Worker for 识字蛇形棋 (https://jinhy1007.github.io/Hanzi-Snake-Ladder/).
//
//   GET  /                 a short-lived (10-minute) Azure Speech token, so the Azure key never reaches the browser
//   POST /sync/new         store a family's learner progress, get a new family sync code back
//   GET  /sync/<code>      read it
//   PUT  /sync/<code>?base=<updated>   replace it (only if nobody else saved since <updated>; otherwise 409)
//
// Setup (Cloudflare dashboard → Workers & Pages → this Worker → Settings):
//   Variables and Secrets:  AZURE_KEY (Secret) = KEY 1 of the Azure Speech resource; AZURE_REGION (Text) = e.g. westus2
//   Bindings:               D1 database, variable name DB → the "hanzi-sync" database (the table is created automatically)
//
// The sync code is the only key to a family's data: nicknames and per-character reading counts, nothing personal.
const ALLOWED = ['https://jinhy1007.github.io', 'http://127.0.0.1:8765', 'http://localhost:8765'];
const CODE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';   // no 0/O, 1/I/L: easy to read out and type
const MAX_BYTES = 400000;

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
      if (url.pathname.startsWith('/sync')) return await sync(request, env, url, cors);
      return await speechToken(env, cors);
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500, cors);
    }
  },
};

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
