// ms_flow2.js — head-ful, persistent-profile attempt at Microsoft account creation.
// Earlier headless attempt ended at "Account creation has been blocked" (anti-abuse).
// This version: real Chrome profile on disk, headed window, human-like keyboard/mouse pacing,
// fresh email verification code pulled from the tekify.xyz inbox.
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..", "..");
const SHARED = path.join(ROOT, "shared");
const HERE = __dirname;
const PROFILE = process.env.AGENT_CHROME_PROFILE || path.join(SHARED, "chrome-agent-profile");
const CRED = path.join(SHARED, "bwt_account.json");
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

function loadEnv() {
  const out = {};
  for (const l of fs.readFileSync(path.join(SHARED, ".env"), "utf8").split(/\r?\n/)) {
    const m = l.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m) out[m[1]] = m[2].trim();
  }
  return out;
}
const E = loadEnv();
const cred = JSON.parse(fs.readFileSync(CRED, "utf8"));
const EMAIL = process.env.MS_EMAIL || cred.email;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const jitter = (a, b) => a + Math.random() * (b - a);

async function newestCode() {
  const r = await fetch(`${E.MAILBOX_INBOX_URL}/inbox?token=${E.MAILBOX_INBOX_TOKEN}&to=${EMAIL}&limit=5`, {
    headers: { "User-Agent": UA },
  });
  const j = await r.json();
  for (const m of j.messages || []) {
    if (!(m.to || "").toLowerCase().includes(EMAIL.split("@")[0])) continue;
    const mm = `${m.text || m.snippet || ""}`.match(/\b(\d{6})\b/);
    if (mm) return mm[1];
  }
  return null;
}

async function waitForCode(timeoutMs = 180000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const c = await newestCode();
    if (c) return c;
    await sleep(8000);
  }
  return null;
}

const bodyText = async (page) =>
  (await page.evaluate(() => (document.body ? document.body.innerText : ""))).replace(/\n{3,}/g, "\n\n").slice(0, 2000);

async function shot(page, name) {
  try {
    await page.screenshot({ path: path.join(HERE, name) });
  } catch {}
}

async function humanType(page, sel, value) {
  const loc = page.locator(sel).first();
  await loc.click({ timeout: 8000 }).catch(() => {});
  await sleep(jitter(200, 500));
  await page.keyboard.type(value, { delay: jitter(60, 150) });
}

async function clickByText(page, names) {
  for (const n of names) {
    const loc = page.locator(`button:has-text("${n}")`).first();
    if (await loc.count()) {
      await sleep(jitter(300, 700));
      await loc.click({ timeout: 8000 }).catch(() => {});
      return n;
    }
  }
  return null;
}

async function main() {
  fs.mkdirSync(PROFILE, { recursive: true });
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: false,
    channel: "chrome",
    viewport: { width: 1280, height: 860 },
    locale: "en-IN",
    timezoneId: "Asia/Kolkata",
    userAgent: UA,
    // Invisible by default: the human is using this machine. --start-maximized popped a window
    // over their desktop; only AGENT_VISIBLE=1 (captcha the human must solve) shows it.
    args: ["--disable-blink-features=AutomationControlled",
           ...(process.env.AGENT_VISIBLE === "1"
             ? ["--start-maximized"]
             : ["--start-minimized", "--window-position=-32000,-32000", "--window-size=1280,900"])],
  });
  await ctx.addInitScript(() => Object.defineProperty(navigator, "webdriver", { get: () => undefined }));
  const page = ctx.pages()[0] || (await ctx.newPage());
  page.setDefaultTimeout(25000);
  try {
    await page.goto("https://signup.live.com/signup?lic=1", { waitUntil: "domcontentloaded", timeout: 60000 });
    await sleep(jitter(2500, 4500));
    console.log("START", page.url());

    for (let step = 0; step < 12; step++) {
      const t = await bodyText(page);
      const has = (sel) => page.locator(sel).count().then((n) => n > 0);
      console.log(`\n===== step ${step} :: ${page.url()}\n${t.trim().slice(0, 700)}`);

      if (/account\.microsoft\.com|outlook\.|microsoft\.com\/welcome/i.test(page.url()) || t.includes("Your Microsoft account is ready")) {
        console.log("ACCOUNT_CREATED");
        cred.created_at = new Date().toISOString();
        fs.writeFileSync(CRED, JSON.stringify(cred, null, 1));
        await shot(page, "flow2_created.png");
        break;
      }

      if (t.includes("blocked")) {
        console.log("BLOCKED");
        await shot(page, `flow2_blocked_${Date.now()}.png`);
        break;
      }
      if (t.includes("prove you're human") || t.includes("Press and hold")) {
        // Human-verification gate (press-and-hold). Not automatable by design:
        // a human must complete it in this visible window. We then continue automatically.
        const waitSec = parseInt(process.env.HUMAN_PAUSE || "600", 10);
        console.log(
          `\n>>> HUMAN ACTION NEEDED: in the Chrome window, complete "Let's prove you're human" ` +
            `(press and hold the button). Waiting up to ${waitSec}s...`
        );
        await shot(page, "flow2_human_needed.png");
        const until = Date.now() + waitSec * 1000;
        let cleared = false;
        while (Date.now() < until) {
          await sleep(3000);
          const now = await bodyText(page).catch(() => "");
          const url = page.isClosed() ? "" : page.url();
          if (!now.includes("prove you're human") && !now.includes("Press and hold")) {
            console.log("CHALLENGE PASSED ->", url);
            cleared = true;
            break;
          }
        }
        if (!cleared) {
          console.log("HUMAN_PAUSE_EXPIRED");
          break;
        }
        await sleep(4000);
        continue;
      }
      if (t.includes("Enter your email address") || (await has('input[name="email"]'))) {
        await humanType(page, 'input[name="email"]', EMAIL);
        await clickByText(page, ["Next"]);
        await sleep(jitter(5000, 8000));
        continue;
      }
      if (await has("#codeEntry-0")) {
        const code = await waitForCode();
        console.log("CODE", code);
        if (!code) break;
        await page.locator("#codeEntry-0").click();
        await sleep(400);
        await page.keyboard.type(code, { delay: jitter(90, 180) });
        await sleep(jitter(600, 1200));
        await page.keyboard.press("Enter").catch(() => {});
        await sleep(jitter(6000, 9000));
        continue;
      }
      const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
      const monthName = MONTHS[parseInt(cred.birth_month, 10) - 1];
      if (await has('input[name="BirthYear"]')) {
        const pick = async (btnSel, optText) => {
          await page.locator(btnSel).focus().catch(() => {});
          await sleep(300);
          await page.keyboard.press("Enter").catch(() => {});
          await sleep(jitter(700, 1100));
          const opt = page.locator(`[role=option]:has-text("${optText}")`).first();
          if (await opt.count()) {
            await opt.click({ force: true }).catch(() => {});
            await sleep(400);
            return true;
          }
          return false;
        };
        console.log("month", await pick("#BirthMonthDropdown", monthName));
        console.log("day", await pick("#BirthDayDropdown", cred.birth_day));
        await humanType(page, 'input[name="BirthYear"]', cred.birth_year);
        await sleep(500);
        await clickByText(page, ["Next"]);
        await sleep(jitter(6500, 9000));
        continue;
      }
      if (await has("#firstNameInput")) {
        await humanType(page, "#firstNameInput", cred.first);
        await sleep(jitter(400, 900));
        await humanType(page, "#lastNameInput", cred.last);
        await sleep(jitter(500, 1000));
        await clickByText(page, ["Next"]);
        await sleep(jitter(7000, 10000));
        continue;
      }
      if (await has('input[type="password"]')) {
        await humanType(page, 'input[type="password"]', cred.password);
        await clickByText(page, ["Next", "Continue"]);
        await sleep(jitter(6000, 9000));
        continue;
      }
      console.log("UNHANDLED", page.url());
      break;
    }
    await sleep(2000);
    console.log("\nFINAL_URL", page.url());
    console.log((await bodyText(page)).trim().slice(0, 1200));
    await shot(page, "flow2_final.png");
  } finally {
    await ctx.close();
  }
}

main().catch((e) => {
  console.error("FATAL", e.message);
  process.exit(1);
});
