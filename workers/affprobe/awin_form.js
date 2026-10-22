const { chromium } = require("playwright");
(async()=>{
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN"});
  const p = await c.newPage();
  const r = await p.goto("https://ui.awin.com/publisher-signup/en/awin/step1",{waitUntil:"networkidle",timeout:60000});
  console.log("STATUS", r.status(), p.url(), "|", await p.title());
  const inputs = await p.$$eval("input,select,textarea", els => els.map(e=>({tag:e.tagName, name:e.name, id:e.id, type:e.type, ph:e.placeholder, req:e.required})));
  console.log(JSON.stringify(inputs,null,0).slice(0,4000));
  const btns = await p.$$eval("button, input[type=submit], a.button", els=>els.map(e=>({t:(e.innerText||e.value||"").trim().slice(0,40), id:e.id, cls:e.className.slice(0,60)})));
  console.log("BTNS", JSON.stringify(btns).slice(0,1200));
  await p.screenshot({path:"awin_step1.png"});
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
