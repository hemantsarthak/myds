const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: false, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  const reqs = [];
  page.on("request", r => { const u=r.url(); if (u.includes("recaptcha")||u.includes("/api/client")) reqs.push(r.method()+" "+u.slice(0,140)); });
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
  await page.click("#profile_personal-info-save-button"); await page.waitForTimeout(2500);
  await page.screenshot({ path: "workers/adsprobe/shots/mon_details.png" });
  // choose Website
  await page.locator('button', { hasText: /^Website$/ }).first().click().catch(async()=>{ await page.locator('text=Website').first().click(); });
  await page.waitForTimeout(1500);
  const all = await page.$$eval("input, textarea, button, [role=checkbox]", els => els.map(e => ({tag:e.tagName, type:e.getAttribute("type"), id:e.id, ph:e.getAttribute("placeholder"), txt:(e.innerText||"").slice(0,50), disabled:e.disabled})));
  console.log("AFTER WEBSITE:", JSON.stringify(all));
  console.log("IFRAMES:", JSON.stringify(page.frames().map(f => f.url()).slice(0,10)));
  const g = await page.$eval("#g-recaptcha-response", el => el ? {v: el.value.length, tag: el.tagName} : null).catch(e=>"ERR "+e.message);
  console.log("GRECAPTCHA:", JSON.stringify(g));
  console.log("SIGNUP DISABLED:", await page.$eval("#profile_personal-info-save-button", b=>b.disabled).catch(()=>"n/a"));
  console.log("REQS:", JSON.stringify(reqs.slice(0,40), null, 1));
  console.log("TEXT:", (await page.innerText("body")).slice(0,1500));
  await page.screenshot({ path: "workers/adsprobe/shots/mon_details2.png" });
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
