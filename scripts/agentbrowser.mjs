// scripts/agentbrowser.mjs — the ONE way repo scripts get a browser.
//
// Behaviour (in order):
//   1. ATTACH to the already-running agent Chrome over CDP (127.0.0.1:9222). Start it once with
//      `scripts/chrome-agent.ps1` and leave it pinned; logins persist and nothing is opened or
//      closed per script run.
//   2. If it is not running, launch the same persistent profile OFF-SCREEN (headful, minimized)
//      because bot-sensitive sites reject headless, but the human must never see it.
//
// Never launch a visible browser from a script: the human is working on this machine. The one
// exception is a captcha/KYC step — use `scripts/chrome-agent.ps1 -Visible` for that, not this.
//
// Usage:
//   import { getBrowser, release } from './agentbrowser.mjs';
//   const h = await getBrowser();            // { browser, context, attached }
//   const page = h.context.pages()[0] || await h.context.newPage();
//   await page.goto(url);
//   await release(h);                        // leaves a pinned/attached browser running
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '..');
export const PROFILE = process.env.AGENT_CHROME_PROFILE || path.join(ROOT, 'shared', 'chrome-agent-profile');
export const CDP_URL = process.env.AGENT_CDP || 'http://127.0.0.1:9222';

export const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

async function attach() {
  try {
    const resp = await fetch(CDP_URL + '/json/version', { signal: AbortSignal.timeout(1500) });
    if (!resp.ok) return null;
    return await chromium.connectOverCDP(CDP_URL);
  } catch {
    return null;
  }
}

/**
 * @param {{headless?: boolean, visible?: boolean, channel?: string, init?: boolean}} opts
 *   visible: ONLY for human-in-the-loop captchas; default false keeps the window off-screen.
 * @returns {Promise<{browser: any, context: any, attached: boolean, close: () => Promise<void>}>}
 */
export async function getBrowser(opts = {}) {
  const attachedBrowser = await attach();
  if (attachedBrowser) {
    let ctx = attachedBrowser.contexts()[0];
    if (!ctx) ctx = await attachedBrowser.newContext();
    if (opts.init !== false) {
      await ctx.addInitScript(() => Object.defineProperty(navigator, 'webdriver', { get: () => undefined })).catch(() => {});
    }
    return {
      browser: attachedBrowser,
      context: ctx,
      attached: true,
      // Drop the DevTools connection, never the browser: a script must not kill the pinned
      // agent Chrome the human/other flows are reusing. Without this the CDP websocket keeps
      // the Node event loop alive and scripts hang after finishing.
      close: async () => { await attachedBrowser.close().catch(() => {}); },
    };
  }

  fs.mkdirSync(PROFILE, { recursive: true });
  const headless = opts.headless === true;              // explicit opt-in only
  const visible = opts.visible === true;                // human-in-the-loop only
  const args = [
    '--disable-blink-features=AutomationControlled',
    '--no-first-run',
    '--no-default-browser-check',
  ];
  if (!headless && !visible) {
    args.push('--start-minimized', '--window-position=-32000,-32000', '--window-size=1280,900');
  } else if (!headless) {
    args.push('--window-size=1366,900', '--window-position=120,80');
  }

  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless,
    channel: opts.channel || process.env.AGENT_CHANNEL || 'chrome',
    viewport: { width: 1280, height: 900 },
    locale: 'en-IN',
    timezoneId: 'Asia/Kolkata',
    userAgent: UA,
    args,
  });
  await ctx.addInitScript(() => Object.defineProperty(navigator, 'webdriver', { get: () => undefined })).catch(() => {});
  return {
    browser: ctx.browser(),
    context: ctx,
    attached: false,
    close: async () => { await ctx.close().catch(() => {}); },
  };
}

/** Convenience: first page (or a new tab) of the agent browser. */
export async function getPage(opts = {}) {
  const handle = await getBrowser(opts);
  const page = handle.context.pages()[0] || await handle.context.newPage();
  page.setDefaultTimeout(30000);
  return { page, ...handle };
}

/** Leaves an attached/pinned browser alone; closes only a browser this script launched. */
export async function release(handle) {
  if (handle && handle.close) await handle.close();
}
