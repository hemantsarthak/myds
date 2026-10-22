const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  const r = await page.goto("https://publishers.adsterra.com/signup", { waitUntil: "domcontentloaded", timeout: 60000 }).catch(e=>{console.log("goto err", e.message.slice(0,100)); return null;});
  console.log("STATUS", r ? r.status() : "n/a", "URL", page.url());
  await page.waitForTimeout(3000);
  console.log("TITLE", await page.title());
  const ctrls = await page.$$eval("input, select, textarea, button, a", els => els.map(e => ({tag:e.tagName, type:e.getAttribute("type"), id:e.id, name:e.getAttribute("name"), ph:e.getAttribute("placeholder"), txt:(e.innerText||"").slice(0,60)})).slice(0,60));
  console.log("CTRLS:", JSON.stringify(ctrls, null, 0).slice(0,5000));
  console.log("TEXT:", (await page.innerText("body")).slice(0,1200));
  console.log("IFRAMES:", JSON.stringify(page.frames().map(f=>f.url().slice(0,100))));
  await page.screenshot({ path: "workers/adsprobe/shots/adsterra_signup.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL", e.message.slice(0,300)); process.exit(1); });
