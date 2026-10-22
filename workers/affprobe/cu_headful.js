const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"cuelinks_pw_state.json"),"utf8"));
  const ctx = await chromium.launchPersistentContext(path.join(__dirname,".pwprofile-cuelinks"), {
    headless:false, channel:"chrome", viewport:{width:1280,height:860}, locale:"en-IN", timezoneId:"Asia/Kolkata",
    args:["--disable-blink-features=AutomationControlled"]});
  const page = ctx.pages()[0] || await ctx.newPage();
  try { await ctx.addCookies(state.cookies); } catch(e){ console.log("cookie inject err", e.message.slice(0,80)); }
  await page.goto("https://www.cuelinks.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  for (let i=0;i<10;i++){ const t=await page.title(); if(!/just a moment/i.test(t)) break; await page.waitForTimeout(4000); }
  console.log("URL", page.url(), "|", await page.title());
  const t=(await page.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n");
  console.log(t.slice(0,2000));
  await page.screenshot({path:path.join(__dirname,"cuelinks_dash2.png")});
  await ctx.storageState({path: path.join(SHARED,"cuelinks_pw_state.json")});
  await ctx.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
