// scripts/session-import.mjs — load saved service logins into the AIProfile Chrome.
//
// The repo already has Playwright "storageState" / cookie dumps for the accounts it created
// (Travelpayouts, Cuelinks, Hostinger, HilltopAds, Microsoft). Re-injecting them into the one
// persistent AIProfile browser means every future session starts logged in without re-running
// password/2FA flows.
//
// It ATTACHES to the running agent Chrome (scripts/chrome-agent.ps1) — start that first.
//
// Usage:
//   node scripts/session-import.mjs            # import + verify
//   node scripts/session-import.mjs --report   # verify only, no import
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getBrowser, release, ROOT } from './agentbrowser.mjs';

const SHARED = path.join(ROOT, 'shared');
const REPORT = process.argv.includes('--report');

// file in shared/ -> where to verify the login
const SERVICES = [
  { name: 'Travelpayouts', file: 'travelpayouts_pw_state.json', url: 'https://www.travelpayouts.com/' },
  { name: 'Cuelinks', file: 'cuelinks_pw_state.json', url: 'https://www.cuelinks.com/dashboard' },
  { name: 'Hostinger', file: 'hostinger_pw_state.json', url: 'https://affiliates.hostinger.com/' },
  { name: 'HilltopAds', file: 'hilltop_cookies.json', url: 'https://user.hilltopads.com/' },
  { name: 'Microsoft', file: 'bwt_pw_state.json', url: 'https://account.microsoft.com/' },
];

const GOOD = /(sign out|log out|logout|dashboard|my account|профиль|balance|campaigns)/i;
const BAD = /(sign in|log in|login|create account|войти)/i;

function sanitizeCookie(c) {
  const sameSite = ['Strict', 'Lax', 'None'].includes(c.sameSite) ? c.sameSite : undefined;
  const out = {
    name: c.name,
    value: c.value,
    domain: c.domain,
    path: c.path || '/',
    expires: typeof c.expires === 'number' ? c.expires : -1,
    httpOnly: !!c.httpOnly,
    secure: !!c.secure,
  };
  if (sameSite) out.sameSite = sameSite;
  return out;
}

function loadCookies(file) {
  const p = path.join(SHARED, file);
  if (!fs.existsSync(p)) return { warn: 'missing' };
  let raw;
  try { raw = JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return { warn: 'unparseable' }; }
  const list = Array.isArray(raw) ? raw : Array.isArray(raw.cookies) ? raw.cookies : null;
  if (!list) return { warn: 'no cookies array' };
  const cookies = list.map(sanitizeCookie).filter((c) => c.name && c.domain);
  return { cookies };
}

const handle = await getBrowser();
const ctx = handle.context;
const results = [];

for (const svc of SERVICES) {
  const entry = { service: svc.name, file: svc.file, imported: 0, status: 'unknown', url: '', title: '' };
  try {
    if (!REPORT) {
      const loaded = loadCookies(svc.file);
      if (loaded.warn) {
        entry.status = 'no-session-file';
        entry.note = loaded.warn;
        results.push(entry);
        continue;
      }
      await ctx.addCookies(loaded.cookies);
      entry.imported = loaded.cookies.length;
    }
    // verify in a dedicated tab so the human's tabs are untouched
    const page = await ctx.newPage();
    try {
      await page.goto(svc.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(2500);
      entry.url = page.url();
      entry.title = (await page.title()).slice(0, 90);
      const text = (await page.locator('body').innerText().catch(() => '')).slice(0, 4000);
      const onAuthPage = /[\/.](login|signin|sign-in|signup|register)([\/?]|$)/i.test(entry.url);
      const signedOut = BAD.test(text) && !/sign out|log out|logout/i.test(text);
      entry.status = onAuthPage || signedOut ? 'logged-out'
        : /sign out|log out|logout/i.test(text) ? 'logged-in'
        : /dashboard|publisher\/sites|account\/home|users\/(edit|dashboard)/i.test(entry.url) && !onAuthPage ? 'logged-in'
        : 'unknown';
    } finally {
      await page.close().catch(() => {});
    }
  } catch (e) {
    entry.status = 'error';
    entry.note = (e && e.message ? e.message : String(e)).slice(0, 140);
  }
  results.push(entry);
  console.log(`${svc.name.padEnd(14)} ${entry.status.padEnd(12)} imported=${String(entry.imported).padEnd(3)} ${entry.url || entry.note || ''}`);
}

console.log('\n' + JSON.stringify(results, null, 2));
await release(handle);
