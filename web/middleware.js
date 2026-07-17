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

// favicon.png is excluded alongside favicon.ico so the login page can show the
// Ode favicon before a session exists. It is branding, not data.
export const config = { matcher: '/((?!favicon.ico|favicon.png).*)' };

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
  // Brand: palette, wordmark and favicon derived from ode.com's live Webflow
  // stylesheet. ABC Diatype is a commercially licensed typeface and is NOT
  // bundled or hotlinked here -- it is named first in the stack so it renders
  // for anyone who has it installed locally, and falls back cleanly otherwise.
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="/favicon.png">
<meta name="robots" content="noindex, nofollow"><title>Welcome to Ode</title>
<script src="https://accounts.google.com/gsi/client" async></script>
<style>:root{--bg:#fbfbf8;--fg:#3c2e2a;--muted:#625855;--line:#e8e4de;--accent:#cd3e1d;
--font-primary:"ABC Diatype",ui-sans-serif,-apple-system,"Helvetica Neue",Arial,sans-serif;
--font-mono:"ABC Diatype Semi Mono",ui-monospace,"SF Mono",Menlo,monospace;
--surface:rgba(255,255,255,.72);
--wash-a:rgba(232,235,215,.55);--wash-b:rgba(244,220,234,.40)}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:radial-gradient(58rem 38rem at 12% -12%,var(--wash-a),transparent 70%),
radial-gradient(46rem 34rem at 96% 4%,var(--wash-b),transparent 72%),var(--bg);
background-attachment:fixed;background-repeat:no-repeat;color:var(--fg);
font-family:var(--font-primary);-webkit-font-smoothing:antialiased}
.box{background:var(--surface);border:1px solid var(--line);border-radius:.5rem;padding:44px 40px;text-align:center;max-width:380px}
.mark{margin:0 0 1.75rem;color:var(--fg);line-height:0;display:flex;justify-content:center}
.mark .wordmark{height:28px;width:auto;display:block}
h2{margin:0 0 10px;font-size:1.5rem;font-weight:500;letter-spacing:-.02em}
p{color:var(--muted);font-size:.9375rem;line-height:1.6;margin:0 0 26px}
.msg{color:var(--accent);font-family:var(--font-mono);font-size:13px;margin-top:14px;min-height:18px}
.g_id_signin{display:flex;justify-content:center}
.foot{color:var(--muted);font-family:var(--font-mono);font-size:.75rem;letter-spacing:.1em;margin:22px 0 0}
/* Ode publishes no dark palette -- this is derived, kept warm around cola. */
@media (prefers-color-scheme:dark){:root{--bg:#201d1c;--fg:#f4f2ed;--muted:#a89e99;
--line:#3a3331;--accent:#e8613f;--surface:rgba(255,255,255,.04);
--wash-a:rgba(232,235,215,.06);--wash-b:rgba(244,220,234,.06)}}</style></head>
<body><div class="box"><div class="mark"><svg class="wordmark" viewBox="0 0 473 98" fill="none" role="img" aria-label="Ode" xmlns="http://www.w3.org/2000/svg"><path d="M0 49.4088C0 76.711 19.7392 90.4862 33.018 97.6841H51.7573C35.7483 89.4934 11.6727 76.8351 11.6727 49.5329V49.2847C11.6727 21.9825 35.7483 9.32421 51.7573 1.13354H33.018C19.7392 8.3314 0 22.1066 0 49.4088ZM30.9011 49.4088C30.9011 72.4916 49.3994 85.6463 61.8095 97.6841H77.0739C57.8382 80.0618 42.6979 66.5347 42.6979 49.4088C42.6979 32.2829 57.8382 18.7559 77.0739 1.13354H61.8095C49.3994 13.1713 30.9011 26.326 30.9011 49.4088ZM64.0361 49.4088C64.0361 69.7614 80.921 88.1283 86.3815 97.6841H99.4121C92.0901 86.515 75.8329 66.6588 75.8329 49.4088C75.8329 32.1588 92.0901 12.3026 99.4121 1.13354H86.3815C80.921 10.6893 64.0361 29.0563 64.0361 49.4088Z" fill="currentColor"/><path d="M116.367 97.6841H105.367V1.13354H116.367V97.6841Z" fill="currentColor"/><path d="M221.734 49.4088C221.734 76.711 201.995 90.4862 188.716 97.6841H169.977C185.986 89.4934 210.062 76.8351 210.062 49.5329V49.2847C210.062 21.9825 185.986 9.32421 169.977 1.13354H188.716C201.995 8.3314 221.734 22.1066 221.734 49.4088ZM190.833 49.4088C190.833 72.4916 172.335 85.6463 159.925 97.6841H144.66C163.896 80.0618 179.036 66.5347 179.036 49.4088C179.036 32.2829 163.896 18.7559 144.66 1.13354H159.925C172.335 13.1713 190.833 26.326 190.833 49.4088ZM157.698 49.4088C157.698 69.7614 140.813 88.1283 135.353 97.6841H122.322C129.644 86.515 145.901 66.6588 145.901 49.4088C145.901 32.1588 129.644 12.3026 122.322 1.13354H135.353C140.813 10.6893 157.698 29.0563 157.698 49.4088Z" fill="currentColor"/><path d="M417.838 68.7529V1.14392H472.592V12.1899H430.598V27.6162H462.864V38.7574H430.598V57.4212H472.592V68.7529H417.838Z" fill="currentColor"/><path d="M340.088 68.7529V1.14392H367.417C389.033 1.14392 403.602 13.523 403.602 34.9484C403.602 55.9929 389.128 68.7529 367.417 68.7529H340.088ZM367.226 12.3803H352.848V57.5165H367.226C381.415 57.5165 390.556 48.8511 390.556 34.9484C390.556 20.5696 381.415 12.3803 367.226 12.3803Z" fill="currentColor"/><path d="M290.424 69.8943C270.141 69.8943 255.001 55.2299 255.001 34.9472C255.001 14.6645 270.332 0 290.424 0C310.516 0 325.847 14.6645 325.847 34.9472C325.847 55.1346 310.516 69.8943 290.424 69.8943ZM290.424 58.277C303.946 58.277 312.802 47.8976 312.802 34.9472C312.802 22.0919 303.946 11.6173 290.424 11.6173C276.998 11.6173 268.142 22.0919 268.142 34.9472C268.142 47.9928 276.902 58.277 290.424 58.277Z" fill="currentColor"/><path d="M322.383 97.7364V82.6554H324.236V88.7524C324.796 87.7614 326.024 87.0073 327.425 87.0073C329.816 87.0073 331.26 88.5154 331.26 91.1869V97.7364H329.407V91.4239C329.407 89.4634 328.739 88.4723 327.059 88.4723C325.292 88.4723 324.236 89.8512 324.236 91.4885V97.7364H322.383Z" fill="currentColor"/><path d="M318.094 97.9087C316.543 97.9087 315.143 97.1547 315.143 94.8495V88.8817H313.204V87.3521H315.143V83.9265H316.996V87.3521H319.15V88.8817H316.996V94.6556C316.996 95.862 317.599 96.2498 318.525 96.2498C318.784 96.2498 318.999 96.2283 319.301 96.1852V97.7795C318.913 97.8657 318.525 97.9087 318.094 97.9087Z" fill="currentColor"/><path d="M308.499 97.7364V87.352H310.352V97.7364H308.499ZM308.327 85.3915V83.1725H310.481V85.3915H308.327Z" fill="currentColor"/><path d="M292.854 97.7364L289.471 87.352H291.475L293.737 95.0433C293.823 95.3019 293.909 95.5604 293.952 95.7543C294.039 95.5173 294.125 95.2803 294.189 95.0433L296.473 87.352H298.778L301.191 95.0433L301.385 95.6681L301.601 95.0003L303.841 87.352H305.716L302.376 97.7364H300.222L297.852 89.8943L297.615 89.1402L297.378 89.8943L294.987 97.7364H292.854Z" fill="currentColor"/><path d="M365.432 93.2326L358.852 82.9074H355.295V97.6443H358.318V87.3191L364.897 97.6443H368.454V82.9074H365.432V93.2326Z" fill="currentColor"/><path d="M370.958 85.7469H375.863V97.6444H379.002V85.7469H383.908V82.9074H370.958V85.7469Z" fill="currentColor"/><path d="M396.43 88.7973H389.549V82.9307H386.41V97.6677H389.549V91.6368H396.43V97.6677H399.569V82.9072H396.43V88.7973Z" fill="currentColor"/><path d="M406.545 85.7467H410.405C411.939 85.7467 412.753 86.3099 412.753 87.3894C412.753 88.4689 411.939 89.0321 410.405 89.0321H406.545V85.7467ZM415.891 87.4129C415.891 84.6203 413.869 82.9308 410.544 82.9308H403.407V97.6678H406.545V91.895H410.033L413.171 97.6678H416.635L413.171 91.4491C414.915 90.7686 415.891 89.3606 415.891 87.4129Z" fill="currentColor"/><path d="M425.481 94.9519C423.017 94.9519 421.506 93.1919 421.506 90.3055C421.506 87.3722 423.017 85.6122 425.481 85.6122C427.922 85.6122 429.41 87.3722 429.41 90.3055C429.41 93.1919 427.922 94.9519 425.481 94.9519ZM425.481 82.6554C421.273 82.6554 418.274 85.8234 418.274 90.3055C418.274 94.7407 421.25 97.9087 425.481 97.9087C429.666 97.9087 432.642 94.7407 432.642 90.3055C432.642 85.8234 429.689 82.6554 425.481 82.6554Z" fill="currentColor"/><path d="M442.569 89.4546H438.71V85.7469H442.569C444.104 85.7469 444.917 86.3805 444.917 87.6007C444.917 88.821 444.127 89.4546 442.569 89.4546ZM442.709 82.9074H435.571V97.6444H438.71V92.3175H442.709C446.033 92.3175 448.056 90.5575 448.056 87.6242C448.056 84.6909 446.033 82.9074 442.709 82.9074Z" fill="currentColor"/><path d="M469.271 92.6991C468.736 94.1305 467.644 94.9519 466.156 94.9519C463.691 94.9519 462.18 93.1919 462.18 90.3055C462.18 87.3722 463.691 85.6122 466.156 85.6122C467.644 85.6122 468.713 86.4335 469.271 87.865H472.596C471.759 84.697 469.317 82.6554 466.156 82.6554C461.948 82.6554 458.948 85.8234 458.948 90.3055C458.948 94.7407 461.924 97.9087 466.156 97.9087C469.341 97.9087 471.782 95.8436 472.596 92.6991H469.271Z" fill="currentColor"/><path d="M449.32 82.9074L455.156 97.6444H458.341L452.505 82.9074H449.32Z" fill="currentColor"/><path d="M343.53 91.8247L345.529 86.6386L347.529 91.8247H343.53ZM343.855 82.9074L338.02 97.6679H341.275L342.46 94.5703H348.552L349.737 97.6679H352.992L347.18 82.9074H343.855Z" fill="currentColor"/></svg></div><h2>Welcome to Ode.</h2>
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
