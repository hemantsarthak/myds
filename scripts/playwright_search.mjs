// scripts/playwright_search.mjs — last-resort search tier for scripts/search.py
//
// Why: some engines only answer a real browser (JS, consent walls, bot checks). This runs a
// headless Chromium through the repo's local Playwright, tries Brave first and Bing second, and
// prints one line of JSON: [{title, url, snippet}, ...]. Exits non-zero when nothing was found so
// the Python chain can fall through to its next tier.
//
// Browser resolution matters: the pinned Playwright may expect a chromium build that is not
// downloaded. Tries, in order: Playwright's own build -> system Chrome (channel) -> any
// chromium-*/chrome-win64/chrome.exe already under ms-playwright -> $PW_CHROMIUM.
//
// Usage: node scripts/playwright_search.mjs "query" [count]
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const query = process.argv[2] || '';
const limit = Math.max(1, parseInt(process.argv[3] || '10', 10));
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
           '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

const ENGINES = [
  {
    name: 'brave',
    url: 'https://search.brave.com/search?q=' + encodeURIComponent(query),
    ready: '#results, .snippet, [data-type="web"]',
    extract: () => Array.from(document.querySelectorAll('#results .snippet, [data-type="web"]')).map((el) => {
      const a = el.querySelector('a[href^="http"]');
      const p = el.querySelector('.snippet-description, .snippet-content, p');
      return { title: (a && a.innerText) || '', url: (a && a.href) || '', snippet: (p && p.innerText) || '' };
    }),
  },
  {
    name: 'bing',
    url: 'https://www.bing.com/search?q=' + encodeURIComponent(query),
    ready: 'li.b_algo',
    extract: () => Array.from(document.querySelectorAll('li.b_algo')).map((el) => {
      const a = el.querySelector('h2 a');
      const p = el.querySelector('p');
      return { title: (a && a.innerText) || '', url: (a && a.href) || '', snippet: (p && p.innerText) || '' };
    }),
  },
];

function installedChromium() {
  const roots = [
    process.env.LOCALAPPDATA ? path.join(process.env.LOCALAPPDATA, 'ms-playwright') : '',
    process.env.USERPROFILE ? path.join(process.env.USERPROFILE, 'AppData', 'Local', 'ms-playwright') : '',
    path.join(os.homedir(), '.cache', 'ms-playwright'),
  ].filter(Boolean);
  const found = [];
  for (const root of roots) {
    let entries = [];
    try { entries = fs.readdirSync(root); } catch { continue; }
    for (const d of entries.filter((x) => x.startsWith('chromium-')).sort().reverse()) {
      for (const rel of ['chrome-win64/chrome.exe', 'chrome-win/chrome.exe', 'chrome-linux/chrome']) {
        const p = path.join(root, d, rel);
        if (fs.existsSync(p)) found.push(p);
      }
    }
  }
  return found;
}

function launchCandidates() {
  const out = [{ label: 'playwright-default', opts: { headless: true } }];
  out.push({ label: 'system-chrome', opts: { headless: true, channel: 'chrome' } });
  out.push({ label: 'system-msedge', opts: { headless: true, channel: 'msedge' } });
  if (process.env.PW_CHROMIUM) {
    out.push({ label: 'PW_CHROMIUM', opts: { headless: true, executablePath: process.env.PW_CHROMIUM } });
  }
  for (const exe of installedChromium()) {
    out.push({ label: path.basename(path.dirname(path.dirname(exe))), opts: { headless: true, executablePath: exe } });
  }
  return out;
}

function dedupe(items) {
  const seen = new Set();
  const out = [];
  for (const r of items) {
    if (!r.url || !/^https?:/i.test(r.url)) continue;
    const key = r.url.split('#')[0].replace(/\/$/, '');
    if (seen.has(key)) continue;
    seen.add(key);
    // Engine layouts prepend the site name and breadcrumb to the anchor text; the last
    // non-empty line is the actual page title.
    const lines = (r.title || '').split('\n').map((s) => s.trim()).filter(Boolean);
    const title = (lines.length ? lines[lines.length - 1] : r.url).trim();
    out.push({ title, url: r.url, snippet: (r.snippet || '').trim() });
    if (out.length >= limit) break;
  }
  return out;
}

let browser = null;
const errors = [];
for (const cand of launchCandidates()) {
  try {
    browser = await chromium.launch(cand.opts);
    break;
  } catch (e) {
    errors.push(`${cand.label}: ${(e && e.message ? e.message.split('\n')[0] : e)}`);
  }
}

if (!browser) {
  console.error('playwright: no usable browser — ' + errors.join(' | '));
  process.exit(1);
}

try {
  const ctx = await browser.newContext({ userAgent: UA, locale: 'en-US', viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  for (const engine of ENGINES) {
    try {
      await page.goto(engine.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForSelector(engine.ready, { timeout: 8000 }).catch(() => {});
      await page.waitForTimeout(700);
      const items = dedupe(await page.evaluate(engine.extract));
      if (items.length) {
        console.log(JSON.stringify(items.slice(0, limit)));
        await browser.close();
        process.exit(0);
      }
    } catch {
      // try the next engine
    }
  }
  await browser.close();
  console.error('playwright: no engine returned results');
  process.exit(1);
} catch (e) {
  try { await browser.close(); } catch { /* ignore */ }
  console.error('playwright: ' + (e && e.message ? e.message : e));
  process.exit(1);
}
