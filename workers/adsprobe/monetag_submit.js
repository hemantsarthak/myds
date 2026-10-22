const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  const api = [];
  page.on("response", async r => {
    const u = r.url();
    if (u.includes("/api/client/") && r.request().method() !== "GET") {
      let body = ""; try { body = (await r.text()).slice(0, 700); } catch(e) { body = "ERR"; }
      api.push({ status: r.status(), method: r.request().method(), url: u.slice(0,120), body });
    }
  });
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
  await page.click("#profile_personal-info-save-button"); await page.waitForTimeout(3000);
  await page.locator('button', { hasText: /Website/ }).first().click(); await page.waitForTimeout(800);
  await page.fill("#signup_select-website", "https://tekify.xyz");
  await page.fill("#signup_source-channel", "Google search");
  await page.fill("#signup_select-experience_description", "This is our first ad network (new publisher).");
  await page.evaluate(() => { const c = document.querySelector("#signup_i-accept"); if (!c.checked) c.click(); });
  await page.waitForTimeout(600);
  // close terms modal if open: click outside / find close
  const modalClose = page.locator('[class*="Terms"] button, [aria-label="Close"], [class*="close"]').first();
  if (await modalClose.count()) { await modalClose.click({ force: true }).catch(()=>{}); await page.waitForTimeout(400); }
  await page.keyboard.press("Escape").catch(()=>{});
  await page.waitForTimeout(400);
  console.log("DISABLED:", await page.$eval("#profile_personal-info-save-button", b=>b.disabled));
  await page.click("#profile_personal-info-save-button", { force: true });
  await page.waitForTimeout(8000);
  console.log("URL AFTER:", page.url());
  console.log("API:", JSON.stringify(api, null, 1).slice(0, 2500));
  console.log("BODY AFTER:", (await page.innerText("body")).slice(0, 1200));
  await page.screenshot({ path: "workers/adsprobe/shots/mon_after_submit.png" });
  await browser.close();
})().catch(e => { console.error("FATAL", e.message.slice(0,300)); process.exit(1); });
