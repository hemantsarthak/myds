const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const cred = JSON.parse(fs.readFileSync(path.join(SHARED,"cuelinks_signup_attempt.json"),"utf8"));
  const browser = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const ctx = await browser.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata"});
  const page = await ctx.newPage();
  await page.goto("https://www.cuelinks.com/login",{waitUntil:"domcontentloaded",timeout:60000});
  await page.waitForTimeout(3000);
  // find the login form and its submit
  const forms = await page.$$eval("form", fs => fs.map(f=>({action:f.action, id:f.id, method:f.method, inputs:[...f.querySelectorAll("input,button")].map(i=>({n:i.name,t:i.type,v:(i.type==="submit"?i.value:"")})).filter(x=>x.n||x.t==="submit")})));
  console.log(JSON.stringify(forms,null,1).slice(0,2500));
  await browser.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
