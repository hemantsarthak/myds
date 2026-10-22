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
  const btn = async (l) => console.log(l, "disabled=", await page.$eval("#profile_personal-info-save-button", b => b.disabled));
  await page.fill("#profile_personal-info-first-name", "Tekify"); await btn("first");
  await page.fill("#profile_personal-info-last-name", "Ads"); await btn("last");
  await page.fill("#profile_personal-info-email", "monetag@tekify.xyz"); await btn("email");
  await page.click("#react-select-3-input"); await page.waitForTimeout(300);
  await page.keyboard.type("India", { delay: 40 }); await page.waitForTimeout(700);
  await page.keyboard.press("Enter"); await page.waitForTimeout(500); await btn("country");
  await page.fill("#profile_personal-info-city", "Mumbai"); await btn("city");
  await page.fill("#profile_personal-info-address", "1 Marine Drive"); await btn("address");
  // messenger = Other, nickname = email
  const cnt = page.locator('#react-select-2-input').locator('xpath=ancestor::div[contains(@class,"container")][1]');
  await cnt.first().click({ force: true }); await page.waitForTimeout(500);
  await page.locator('[class*="option"]', { hasText: "Other" }).first().click(); await page.waitForTimeout(600);
  await page.fill("#signup_messenger-input-messenger", "ads@tekify.xyz"); await btn("messenger");
  await page.fill("#profile_personal-info-phone-number", "9876543210"); await btn("phone");
  await page.screenshot({ path: "workers/adsprobe/shots/monetag_filled.png", fullPage: true });
  console.log("TEXT:", (await page.innerText("body")).slice(0, 900));
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
