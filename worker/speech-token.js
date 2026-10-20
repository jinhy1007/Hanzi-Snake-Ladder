// Cloudflare Worker for 识字蛇形棋: hands the game a short-lived (10-minute) Azure Speech token,
// so the Azure key itself never reaches the browser.
//
// Setup (Cloudflare dashboard → Workers & Pages → this Worker → Settings → Variables and Secrets):
//   AZURE_KEY     type "Secret": KEY 1 from the Azure Speech resource (Keys and Endpoint)
//   AZURE_REGION  type "Text":   the resource's region, e.g. eastus
//
// Only pages on the sites below may ask for a token.
const ALLOWED = ['https://jinhy1007.github.io', 'http://127.0.0.1:8765', 'http://localhost:8765'];

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const ok = ALLOWED.includes(origin);
    const cors = { 'Access-Control-Allow-Origin': ok ? origin : ALLOWED[0], 'Vary': 'Origin', 'Cache-Control': 'no-store' };
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: { ...cors, 'Access-Control-Allow-Methods': 'GET', 'Access-Control-Max-Age': '86400' } });
    }
    if (!ok) return new Response('Forbidden', { status: 403, headers: cors });
    if (!env.AZURE_KEY || !env.AZURE_REGION) return new Response('Worker is missing AZURE_KEY or AZURE_REGION', { status: 500, headers: cors });

    const r = await fetch(`https://${env.AZURE_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken`, {
      method: 'POST',
      headers: { 'Ocp-Apim-Subscription-Key': env.AZURE_KEY },
    });
    if (!r.ok) return new Response(`Azure said ${r.status}`, { status: 502, headers: cors });
    return new Response(JSON.stringify({ token: await r.text(), region: env.AZURE_REGION }), {
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  },
};
