const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2000);
  const ok = page.locator('text=OK, THANKS'); if (await ok.count()) { await ok.first().click().catch(()=>{}); await page.waitForTimeout(400); }
  await page.click("#create-account-with-email-button"); await page.waitForTimeout(1200);
  await page.fill("#profile_personal-info-first-name", "Tekify");
  await page.fill("#profile_personal-info-last-name", "Ads");
  await page.fill("#profile_personal-info-email", "monetag@tekify.xyz");
  const btn = async (l) => console.log(l, "disabled=", await page.$eval("#profile_personal-info-save-button", b => b.disabled));
  // country select: click and type
  await page.click("#react-select-3-input");
  await page.waitForTimeout(500);
  await page.keyboard.type("India", { delay: 60 });
  await page.waitForTimeout(900);
  const opts = await page.$$eval('[class*="option"]', els => els.map(e => (e.innerText||"").trim()).slice(0,10));
  console.log("COUNTRY OPTS:", JSON.stringify(opts));
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  await btn("country");
  // messenger select
  await page.click("#react-select-2-input");
  await page.waitForTimeout(700);
  const mopts = await page.$$eval('[class*="option"]', els => els.map(e => (e.innerText||"").trim()).slice(0,15));
  console.log("MESSENGER OPTS:", JSON.stringify(mopts));
  await page.screenshot({ path: "workers/adsprobe/shots/monetag_form2.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
