// pw.js — tiny Playwright helper for affiliate-program probes (Node, local chromium)
// Usage: node pw.js login-cuelinks | dump <url> | shot <url> <out.png>
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");
const ROOT = path.resolve(__dirname, "..", "..");
const SHARED = path.join(ROOT, "shared");

async function newCtx(headless = true) {
  const browser = await chromium.launch({ headless, channel: "chrome", args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    viewport: { width: 1366, height: 900 }, locale: "en-IN", timezoneId: "Asia/Kolkata",
  });
  return { browser, ctx };
}
const loadJson = (p) => JSON.parse(fs.readFileSync(path.join(SHARED, p), "utf8"));

async function text(page) {
  return (await page.evaluate(() => document.body ? document.body.innerText : "")).replace(/\n{3,}/g, "\n\n");
}

async function main() {
  const [cmd, ...args] = process.argv.slice(2);
  if (cmd === "dump") {
    const { browser, ctx } = await newCtx();
    const page = await ctx.newPage();
    const r = await page.goto(args[0], { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3000);
    console.log("STATUS", r && r.status(), page.url());
    console.log("TITLE", await page.title());
    console.log(await text(page));
    await browser.close();
    return;
  }
  if (cmd === "cuelinks-login") {
    const cred = loadJson("cuelinks_signup_attempt.json");
    const { browser, ctx } = await newCtx();
    const page = await ctx.newPage();
    await page.goto("https://www.cuelinks.com/login", { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(4000);
    console.log("BEFORE", page.url(), await page.title());
    await page.fill("#email", cred.email).catch(()=>{});
    await page.fill("#password", cred.password).catch(()=>{});
    await Promise.all([page.waitForLoadState("domcontentloaded").catch(()=>{}), page.click('button[type=submit], input[type=submit]').catch(()=>{})]);
    await page.waitForTimeout(5000);
    console.log("AFTER", page.url(), await page.title());
    console.log(await text(page));
    const cookies = await ctx.cookies();
    fs.writeFileSync(path.join(SHARED, "cuelinks_pw_cookies.json"), JSON.stringify(cookies, null, 1));
    fs.writeFileSync(path.join(SHARED, "cuelinks_pw_state.json"), JSON.stringify(await ctx.storageState(), null, 1));
    await page.screenshot({ path: path.join(__dirname, "cuelinks_after_login.png"), fullPage: false });
    await browser.close();
    return;
  }
  console.log("unknown cmd", cmd);
}
main().catch(e => { console.error("FATAL", e.message); process.exit(1); });

