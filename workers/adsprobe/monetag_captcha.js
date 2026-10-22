const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2500);
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
  await page.click("#profile_personal-info-save-button"); await page.waitForTimeout(3500);
  // find recaptcha anchor iframe and click checkbox
  const anchor = page.frames().find(f => f.url().includes("recaptcha/api2/anchor"));
  console.log("anchor found:", !!anchor, anchor ? anchor.url().slice(0,80) : "");
  if (anchor) {
    const box = await anchor.frameElement().then(el => el.boundingBox());
    console.log("anchor box:", JSON.stringify(box));
    const cb = await anchor.$(".recaptcha-checkbox-border");
    console.log("checkbox el:", !!cb);
    if (box) {
      // click the checkbox area (left ~27px center)
      await page.mouse.move(box.x + box.width/2, box.y + box.height/2, { steps: 8 });
      await page.waitForTimeout(300);
      await page.mouse.click(box.x + 28, box.y + 30);
    }
    await page.waitForTimeout(4000);
    const bframe = page.frames().find(f => f.url().includes("bframe"));
    console.log("bframe challenge present:", !!bframe, bframe ? bframe.url().slice(0,60) : "");
    if (bframe) {
      const txt = await bframe.evaluate(() => document.body ? document.body.innerText.slice(0,200) : "").catch(e=>"ERR");
      console.log("BF TEXT:", txt);
    }
    const g = await page.$eval("#g-recaptcha-response", el => el.value.length).catch(()=>-1);
    console.log("g-recaptcha-response len:", g);
    await page.screenshot({ path: "workers/adsprobe/shots/mon_captcha.png" });
  }
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
