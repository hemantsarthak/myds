const { chromium } = require("playwright");
(async()=>{
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata"});
  const p = await c.newPage();
  const url = "https://passport.travelpayouts.com/registration?client_id=b0e02fcc-0ab4-4b2c-a164-742762783a4e&response_type=code&redirect_uri=https%3A%2F%2Fapp.travelpayouts.com%2Fapi%2Fauth%2Fcallback&locale=en";
  const r = await p.goto(url,{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(4000);
  console.log("STATUS", r.status(), p.url(), "|", await p.title());
  const fields = await p.$$eval("input,select,textarea,button", els=>els.map(e=>({t:e.tagName,n:e.name,i:e.id,ty:e.type,txt:(e.innerText||e.value||"").trim().slice(0,40), ph:e.placeholder||""})));
  console.log(JSON.stringify(fields,null,0).slice(0,3500));
  console.log("TEXT:", (await p.evaluate(()=>document.body.innerText)).slice(0,800));
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
