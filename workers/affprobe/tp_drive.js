const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(4000);
  const t = await p.$('text=Manual installation');
  if (t) { await t.click().catch(e=>console.log("click err",e.message.slice(0,80))); await p.waitForTimeout(6000); }
  console.log("URL", p.url());
  console.log((await p.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n").slice(0,2500));
  // grab textarea/code content
  const codes = await p.$$eval("textarea, pre, code", els=>els.map(e=>e.value||e.innerText).filter(Boolean).slice(0,10));
  console.log("CODES:", JSON.stringify(codes).slice(0,1500));
  fs.writeFileSync(path.join(SHARED,"travelpayouts_pw_state.json"), JSON.stringify(await c.storageState(),null,1));
  await p.screenshot({path:path.join(__dirname,"tp_drive.png"), fullPage:false});
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
