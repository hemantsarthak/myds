const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2000);
  const ok = page.locator('text=OK, THANKS'); if (await ok.count()) { await ok.first().click().catch(()=>{}); await page.waitForTimeout(400); }
  await page.click("#create-account-with-email-button"); await page.waitForTimeout(1200);
  await page.fill("#profile_personal-info-first-name", "Tekify");
  await page.fill("#profile_personal-info-last-name", "Ads");
  await page.fill("#profile_personal-info-email", "monetag@tekify.xyz");
  await page.click("#react-select-3-input"); await page.waitForTimeout(400);
  await page.keyboard.type("India", { delay: 50 }); await page.waitForTimeout(800);
  await page.keyboard.press("Enter"); await page.waitForTimeout(400);
  // click messenger container by its label proximity: find div with text 'Messenger' then sibling select container
  const container = page.locator('#react-select-2-input').locator('xpath=ancestor::div[contains(@class,"container")][1]');
  const cnt = await container.count();
  console.log("messenger container count", cnt);
  if (cnt) { await container.first().click({ force: true }); await page.waitForTimeout(800); }
  const mopts = await page.$$eval('[class*="option"]', els => els.map(e => (e.innerText||"").trim()).slice(0,15));
  console.log("MESSENGER OPTS:", JSON.stringify(mopts));
  await page.screenshot({ path: "workers/adsprobe/shots/monetag_form3.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
