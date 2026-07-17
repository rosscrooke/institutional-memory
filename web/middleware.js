// Vercel Edge Middleware — server-side Google sign-in gate for the static directory.
//
// Runs before any file is served, so curl / View Source / incognito are all blocked
// until the visitor proves an @fractional.ai Google login. Flow:
//   1. Unauthenticated request -> we return a "Sign in with Google" page (never the data).
//   2. Google posts the signed ID token to /__auth; we verify its signature against
//      Google's public keys, the audience, and the @fractional.ai domain.
//   3. We set our own HMAC-signed session cookie; later requests skip Google and just
//      verify that cookie (fast, no network).
//
// Required env var: SESSION_SECRET (any long random string). Fail-closed without it.
// GOOGLE_CLIENT_ID defaults to the directory's OAuth client; override via env if needed.

export const config = { matcher: '/((?!favicon.ico).*)' };

const CLIENT_ID = process.env.GOOGLE_CLIENT_ID ||
  '1026575660092-u1pgj4osm40g90b4be4ici1e1afbo297.apps.googleusercontent.com';
// A SET, not a single value. ode.com is the public website; Workspace email is
// still @fractional.ai as of 2026-07-17. Dropping fractional.ai would lock out
// the entire company. Accepting both makes the eventual migration a config
// change rather than an outage. Override via ALLOWED_DOMAINS (comma-separated).
const ALLOWED_DOMAINS = (process.env.ALLOWED_DOMAINS || 'fractional.ai,ode.com')
  .split(',')
  .map(d => d.trim().toLowerCase())
  .filter(Boolean);
const SESSION_TTL = 12 * 60 * 60; // seconds
const COOKIE = 'fai_session';
const enc = new TextEncoder();
const dec = new TextDecoder();

function b64urlToBytes(s) {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
function bytesToB64url(bytes) {
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function jsonFromB64url(s) {
  return JSON.parse(dec.decode(b64urlToBytes(s)));
}

async function hmac(secret, data) {
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(data));
  return bytesToB64url(new Uint8Array(sig));
}

async function makeSession(email, secret) {
  const payload = bytesToB64url(enc.encode(JSON.stringify(
    { email, exp: Math.floor(Date.now() / 1000) + SESSION_TTL })));
  return payload + '.' + (await hmac(secret, payload));
}
async function verifySession(token, secret) {
  if (!token || !token.includes('.')) return null;
  const [payload, sig] = token.split('.');
  if (sig !== (await hmac(secret, payload))) return null;
  try {
    const data = jsonFromB64url(payload);
    if (!data.exp || data.exp < Math.floor(Date.now() / 1000)) return null;
    return data;
  } catch { return null; }
}

let jwksCache = null, jwksAt = 0;
async function getJwks() {
  if (jwksCache && Date.now() - jwksAt < 3600_000) return jwksCache;
  const res = await fetch('https://www.googleapis.com/oauth2/v3/certs');
  jwksCache = (await res.json()).keys;
  jwksAt = Date.now();
  return jwksCache;
}
async function verifyGoogleIdToken(jwt) {
  const parts = jwt.split('.');
  if (parts.length !== 3) return null;
  const [h, p, s] = parts;
  let header;
  try { header = jsonFromB64url(h); } catch { return null; }
  const jwk = (await getJwks()).find(k => k.kid === header.kid);
  if (!jwk) return null;
  const key = await crypto.subtle.importKey(
    'jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  const ok = await crypto.subtle.verify(
    'RSASSA-PKCS1-v1_5', key, b64urlToBytes(s), enc.encode(h + '.' + p));
  if (!ok) return null;
  const c = jsonFromB64url(p);
  const now = Math.floor(Date.now() / 1000);
  if (c.aud !== CLIENT_ID) return null;
  if (!['accounts.google.com', 'https://accounts.google.com'].includes(c.iss)) return null;
  if (c.exp < now) return null;
  if (!c.email || c.email_verified !== true) return null;
  const domain = (c.hd || c.email.split('@')[1] || '').toLowerCase();
  if (!ALLOWED_DOMAINS.includes(domain)) return null;
  return c;
}

function parseCookies(str) {
  const out = {};
  (str || '').split(';').forEach(p => {
    const i = p.indexOf('=');
    if (i > 0) out[p.slice(0, i).trim()] = p.slice(i + 1).trim();
  });
  return out;
}

function loginPage(message) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Welcome to Ode</title>
<script src="https://accounts.google.com/gsi/client" async></script>
<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#faf9f7;color:#1a1a1a;
font-family:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
-webkit-font-smoothing:antialiased}
.box{background:#fff;border:1px solid #e5e2dd;border-radius:14px;padding:44px 40px;text-align:center;max-width:380px}
.mark{font-size:1.75rem;font-weight:500;letter-spacing:-.03em;margin:0 0 1.75rem;color:#1a1a1a}
h2{margin:0 0 10px;font-size:1.5rem;font-weight:500;letter-spacing:-.02em}
p{color:#6b6b6b;font-size:.9375rem;line-height:1.6;margin:0 0 26px}
.msg{color:#b4342a;font-size:13px;margin-top:14px;min-height:18px}
.g_id_signin{display:flex;justify-content:center}
.foot{color:#9a9895;font-size:.75rem;margin:22px 0 0}
@media (prefers-color-scheme:dark){body{background:#141413;color:#f5f4f2}
.box{background:#1c1b1a;border-color:#2e2d2b}.mark{color:#f5f4f2}p{color:#9a9895}}</style></head>
<body><div class="box"><div class="mark">[</div><h2>Welcome to Ode.</h2>
<p>Sign in to start your first week.</p>
<div id="g_id_onload" data-client_id="${CLIENT_ID}" data-login_uri="/__auth" data-auto_select="true"></div>
<div class="g_id_signin" data-type="standard" data-theme="filled_blue" data-size="large" data-width="280"></div>
<div class="msg">${message || ''}</div></div></body></html>`;
}
function htmlResponse(body, status) {
  return new Response(body, { status, headers: { 'content-type': 'text/html; charset=utf-8' } });
}

export default async function middleware(request) {
  const url = new URL(request.url);
  const secret = process.env.SESSION_SECRET;
  if (!secret) {
    return htmlResponse(loginPage('Sign-in is not configured yet (SESSION_SECRET unset).'), 503);
  }

  // Google posts the ID token here after a successful sign-in.
  if (url.pathname === '/__auth' && request.method === 'POST') {
    const form = new URLSearchParams(await request.text());
    const credential = form.get('credential');
    const csrfBody = form.get('g_csrf_token');
    const csrfCookie = parseCookies(request.headers.get('cookie'))['g_csrf_token'];
    if (!credential || !csrfBody || csrfBody !== csrfCookie) {
      return htmlResponse(loginPage('Sign-in failed (CSRF check). Please try again.'), 400);
    }
    const claims = await verifyGoogleIdToken(credential);
    if (!claims) {
      return htmlResponse(loginPage('Access is restricted to @fractional.ai accounts.'), 403);
    }
    const session = await makeSession(claims.email, secret);
    return new Response(null, {
      status: 302,
      headers: {
        location: '/',
        'set-cookie': `${COOKIE}=${session}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${SESSION_TTL}`,
      },
    });
  }

  if (url.pathname === '/__logout') {
    return new Response(null, {
      status: 302,
      headers: { location: '/', 'set-cookie': `${COOKIE}=; Path=/; Max-Age=0` },
    });
  }

  const session = await verifySession(parseCookies(request.headers.get('cookie'))[COOKIE], secret);
  if (session) return; // authenticated -> serve the requested static file

  return htmlResponse(loginPage(''), 401); // never serve the data to anonymous visitors
}
