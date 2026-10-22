// ms_flow.js — drive Microsoft account creation with an existing email, end to end.
// Steps discovered from recon: signup.live.com -> Email -> "Verify your email" 6-digit code
// (mail lands in the tekify.xyz inbox) -> password -> name -> birthdate -> done.
// Polls the autonomous inbox over HTTP; dumps every step so failures are diagnosable.
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..", "..");
const SHARED = path.join(ROOT, "shared");
const HERE = __dirname;
const STATE = path.join(SHARED, "bwt_pw_state.json");
const CRED = path.join(SHARED, "bwt_account.json");

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

function loadEnv() {
  const txt = fs.readFileSync(path.join(SHARED, ".env"), "utf8");
  const env = {};
  for (const line of txt.split(/\r?\n/)) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m) env[m[1]] = m[2].trim();
  }
  return env;
}

function loadCred() {
  if (fs.existsSync(CRED)) return JSON.parse(fs.readFileSync(CRED, "utf8"));
  const c = {
    email: "bingwmt@tekify.xyz",
    password: process.env.MS_PASSWORD || "Tekify!Wmt#2026x",
    first: "Bing",
    last: "Wmt",
    birth_month: "3",
    birth_day: "12",
    birth_year: "1990",
    created_at: null,
  };
  fs.writeFileSync(CRED, JSON.stringify(c, null, 1));
  return c;
}

const ENV = loadEnv();
const CRED_DATA = loadCred();
const T0 = Date.now();

async function mailCodes() {
  const url = `${ENV.MAILBOX_INBOX_URL}/inbox?token=${ENV.MAILBOX_INBOX_TOKEN}&to=${CRED_DATA.email}&limit=6`;
  const r = await fetch(url, { headers: { "User-Agent": UA } });
  if (!r.ok) return [];
  const j = await r.json();
  const msgs = j.messages || j || [];
  const out = [];
  for (const m of msgs) {
    const blob = `${m.subject || ""}\n${m.text || ""}\n${m.snippet || ""}`;
    for (const mm of blob.matchAll(/\b(\d{6})\b/g)) {
      out.push({ code: mm[1], at: m.received_at, subject: m.subject });
    }
  }
  return out;
}

async function waitForCode(timeoutMs = 150000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const codes = await mailCodes();
    if (codes.length) {
      console.log("MAIL CODES", JSON.stringify(codes.slice(0, 3)));
      return codes[0].code;
    }
    await new Promise((r) => setTimeout(r, 8000));
  }
  return null;
}

const text = async (page) =>
  (await page.evaluate(() => (document.body ? document.body.innerText : ""))).replace(/\n{3,}/g, "\n\n").slice(0, 2500);

async function dump(page, tag) {
  const info = await page.evaluate(() => ({
    url: location.href,
    title: document.title,
    inputs: Array.from(document.querySelectorAll("input,select"))
      .filter((e) => e.getBoundingClientRect().height > 0)
      .map((e) => ({ type: e.type, id: e.id, name: e.name, ph: e.placeholder, al: e.getAttribute("aria-label") })),
    buttons: Array.from(document.querySelectorAll("button,[role=button],input[type=submit]"))
      .filter((b) => b.getBoundingClientRect().height > 0)
      .map((b) => ((b.innerText || b.value || b.getAttribute("aria-label") || "").trim() || b.id).slice(0, 50)),
    iframes: Array.from(document.querySelectorAll("iframe")).map((f) => f.src || f.id || "about:blank").slice(0, 6),
  }));
  console.log(`\n===== ${tag} :: ${info.url}\n${info.title}`);
  console.log((await text(page)).trim());
  console.log("INPUTS", JSON.stringify(info.inputs));
  console.log("BUTTONS", JSON.stringify(info.buttons));
  if (info.iframes.length) console.log("IFRAMES", JSON.stringify(info.iframes));
  try {
    await page.screenshot({ path: path.join(HERE, `flow_${tag}.png`) });
  } catch {}
  return info;
}

async function clickText(page, names) {
  for (const n of names) {
    const loc = page.locator(`button:has-text("${n}"), [role=button]:has-text("${n}"), input[type=submit][value="${n}"]`).first();
    if (await loc.count()) {
      await loc.click({ timeout: 5000 }).catch(() => {});
      return n;
    }
  }
  return null;
}

async function main() {
  const cmd = process.argv[2] || "flow";
  const browser = await chromium.launch({
    headless: process.env.HEADFUL ? false : true,
    channel: "chrome",
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const opts = {
    userAgent: UA,
    viewport: { width: 1366, height: 900 },
    locale: "en-US",
    timezoneId: "Asia/Kolkata",
  };
  if (fs.existsSync(STATE)) opts.storageState = STATE;
  const c = await browser.newContext(opts);
  await c.addInitScript(() => Object.defineProperty(navigator, "webdriver", { get: () => undefined }));
  const page = await c.newPage();
  page.setDefaultTimeout(20000);

  try {
    await page.goto("https://signup.live.com/signup?lic=1", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(3000);

    for (let step = 0; step < 9; step++) {
      const info = await dump(page, `s${step}`);
      const has = (sel) => page.locator(sel).count().then((n) => n > 0);

      if (info.url.includes("signup.live.com") && (await has('input[name="email"]'))) {
        // Step 1: submit the existing email address
        await page.fill('input[name="email"]', CRED_DATA.email);
        await clickText(page, ["Next"]);
        await page.waitForTimeout(6000);
        continue;
      }

      if (await has('#codeEntry-0, input[aria-label*="code digit"]')) {
        // Step 2: email verification code
        const code = await waitForCode();
        if (!code) {
          console.log("NO_CODE_RECEIVED");
          break;
        }
        console.log("USING CODE", code);
        for (let i = 0; i < 6; i++) {
          await page.fill(`#codeEntry-${i}`, code[i]).catch(async () => {
            const els = page.locator('input[aria-label*="code digit"]');
            await els.nth(i).fill(code[i]);
          });
        }
        await page.waitForTimeout(500);
        await page.keyboard.press("Enter").catch(() => {});
        await clickText(page, ["Next", "Verify", "Continue"]);
        await page.waitForTimeout(7000);
        continue;
      }

      if (await has('input[type="password"]')) {
        // Step 3: password
        await page.fill('input[type="password"]', CRED_DATA.password);
        await clickText(page, ["Next", "Continue"]);
        await page.waitForTimeout(6000);
        continue;
      }

      if ((await has("#firstNameInput")) || (await has('input[name="firstName"]'))) {
        // Step 4: name
        await page.fill("#firstNameInput", CRED_DATA.first).catch(() => {});
        await page.fill("#lastNameInput", CRED_DATA.last).catch(() => {});
        await page.fill('input[name="firstName"]', CRED_DATA.first).catch(() => {});
        await page.fill('input[name="LastName"]', CRED_DATA.last).catch(() => {});
        await page.fill('input[name="lastName"]', CRED_DATA.last).catch(() => {});
        await clickText(page, ["Next", "Continue"]);
        await page.waitForTimeout(7500);
        continue;
      }

      if ((await has('input[name="BirthYear"]')) || (await text(page)).includes("Add some details")) {
        // Step 5: birthdate — Fluent UI dropdowns (#BirthMonthDropdown, #BirthDayDropdown) + year input
        const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
        const monthName = MONTHS[parseInt(CRED_DATA.birth_month, 10) - 1] || "March";
        const openPick = async (btnSel, optionText) => {
          const btn = page.locator(btnSel);
          await btn.focus().catch(() => {});
          await page.keyboard.press("Enter").catch(() => {});
          await page.waitForTimeout(900);
          let opt = page.locator(`[role=option]:has-text("${optionText}")`).first();
          if (await opt.count()) {
            await opt.click({ force: true, timeout: 5000 }).catch(() => {});
            return true;
          }
          // fallback: typeahead
          await btn.focus().catch(() => {});
          await page.keyboard.type(optionText, { delay: 40 }).catch(() => {});
          await page.waitForTimeout(400);
          await page.keyboard.press("Enter").catch(() => {});
          return false;
        };
        const mOk = await openPick("#BirthMonthDropdown", monthName);
        console.log("month picked", mOk, monthName);
        const dOk = await openPick("#BirthDayDropdown", CRED_DATA.birth_day);
        console.log("day picked", dOk, CRED_DATA.birth_day);
        await page.fill('input[name="BirthYear"]', CRED_DATA.birth_year).catch((e) => console.log("year err", e.message));
        await page.waitForTimeout(400);
        await clickText(page, ["Next", "Continue"]);
        await page.waitForTimeout(7500);
        continue;
      }

      // Unknown page (captcha, error, or done) — dump form HTML so we can adapt
      console.log("UNHANDLED_STEP", info.url);
      console.log(
        "FORM_HTML",
        await page.evaluate(() => {
          const f = document.querySelector("form") || document.body;
          return (f.outerHTML || "").replace(/<svg[\s\S]*?<\/svg>/g, "").slice(0, 7000);
        })
      );
      break;
    }
    await dump(page, "final");
    fs.writeFileSync(STATE, JSON.stringify(await c.storageState(), null, 1));
    console.log("STATE_SAVED");
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error("FATAL", e.message);
  process.exit(1);
});
