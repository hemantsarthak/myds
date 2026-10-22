const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
  // dismiss cookie banner
  const ok = page.locator('text=OK, THANKS');
  if (await ok.count()) { await ok.first().click().catch(()=>{}); await page.waitForTimeout(500); }
  await page.click("#create-account-with-email-button");
  await page.waitForTimeout(2000);
  fs.mkdirSync("workers/adsprobe/shots", { recursive: true });
  await page.screenshot({ path: "workers/adsprobe/shots/monetag_email_form.png", fullPage: true });
  const controls = await page.$$eval("input, select, textarea, button, [role=combobox]", els => els.map(e => ({tag:e.tagName, type:e.getAttribute("type"), name:e.getAttribute("name"), id:e.id, ph:e.getAttribute("placeholder"), aria:e.getAttribute("aria-label"), txt:(e.innerText||"").slice(0,50)})));
  console.log(JSON.stringify(controls, null, 1).slice(0,6000));
  console.log("TEXT:", (await page.innerText("body")).slice(0,2500));
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
