const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(5000);
  const els = await p.$$eval("a,button,[role=button],[class*=card],[class*=option]", els=>els.map(e=>({t:(e.innerText||"").trim().slice(0,50), tag:e.tagName, cls:(e.className||"").toString().slice(0,70), href:e.href||""})).filter(x=>x.t));
  console.log(JSON.stringify(els.slice(0,40),null,1));
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
