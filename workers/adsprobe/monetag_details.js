const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2000);
  const ok = page.locator('text=OK, THANKS'); if (await ok.count()) { await ok.first().click().catch(()=>{}); await page.waitForTimeout(300); }
  await page.click("#create-account-with-email-button"); await page.waitForTimeout(1000);
  await page.fill("#profile_personal-info-first-name", "Tekify");
  await page.fill("#profile_personal-info-last-name", "Ads");
  await page.fill("#profile_personal-info-email", "monetag@tekify.xyz");
  await page.click("#react-select-3-input"); await page.waitForTimeout(300);
  await page.keyboard.type("India", { delay: 40 }); await page.waitForTimeout(700);
  await page.keyboard.press("Enter"); await page.waitForTimeout(500);
  await page.fill("#profile_personal-info-city", "Mumbai");
  await page.fill("#profile_personal-info-address", "1 Marine Drive");
  const cnt = page.locator('#react-select-2-input').locator('xpath=ancestor::div[contains(@class,"container")][1]');
  await cnt.first().click({ force: true }); await page.waitForTimeout(500);
  await page.locator('[class*="option"]', { hasText: "Other" }).first().click(); await page.waitForTimeout(500);
  await page.fill("#signup_messenger-input-messenger", "ads@tekify.xyz");
  await page.click("#profile_personal-info-save-button"); await page.waitForTimeout(2500);
  const ctrls = await page.$$eval("input, select, textarea, button, [role=checkbox]", els => els.map(e => ({tag:e.tagName, type:e.getAttribute("type"), id:e.id, ph:e.getAttribute("placeholder"), txt:(e.innerText||"").slice(0,40), disabled:e.disabled})));
  console.log("DETAILS CTRLS:", JSON.stringify(ctrls, null, 0));
  console.log("TEXT:", (await page.innerText("body")).slice(0,1200));
  await page.screenshot({ path: "workers/adsprobe/shots/monetag_details.png", fullPage: true });
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
