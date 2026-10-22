const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const cred = JSON.parse(fs.readFileSync(path.join(SHARED,"cuelinks_signup_attempt.json"),"utf8"));
  const browser = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const ctx = await browser.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata"});
  const page = await ctx.newPage();
  await page.goto("https://www.cuelinks.com/login",{waitUntil:"domcontentloaded",timeout:60000});
  await page.waitForTimeout(2500);
  await page.fill('form[action$="/login"] input[name=email]', cred.email);
  await page.fill('form[action$="/login"] input[name=password]', cred.password);
  await Promise.all([
    page.waitForLoadState("domcontentloaded").catch(()=>{}),
    page.click('form[action$="/login"] button[type=submit]'),
  ]);
  await page.waitForTimeout(5000);
  console.log("AFTER", page.url());
  console.log("TITLE", await page.title());
  const t = (await page.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n");
  console.log(t.slice(0,2500));
  fs.writeFileSync(path.join(SHARED,"cuelinks_pw_state.json"), JSON.stringify(await ctx.storageState(),null,1));
  await page.screenshot({path:path.join(__dirname,"cuelinks_dash.png")});
  await browser.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
