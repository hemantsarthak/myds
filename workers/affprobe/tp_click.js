const { chromium } = require("playwright");
(async()=>{
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN"});
  const p = await c.newPage();
  await p.goto("https://www.travelpayouts.com/",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(3000);
  const links = await p.$$eval("a", as=>as.map(a=>({t:(a.innerText||"").trim().slice(0,40),h:a.href})).filter(x=>/sign|join|register|start/i.test(x.t+x.h)).slice(0,15));
  console.log(JSON.stringify(links,null,1));
  // try clicking first signup
  const btn = await p.$('a:has-text("Sign up"), a:has-text("Join"), a:has-text("Sign Up")');
  if (btn) { await Promise.all([p.waitForLoadState("domcontentloaded").catch(()=>{}), btn.click().catch(()=>{})]); await p.waitForTimeout(4000); console.log("AFTER CLICK", p.url()); }
  const inputs = await p.$$eval("input,button[type=submit]", els=>els.map(e=>({t:e.tagName,n:e.name,i:e.id,ty:e.type,txt:(e.innerText||e.value||"").slice(0,30)})));
  console.log(JSON.stringify(inputs).slice(0,1500));
  await p.screenshot({path:"tp_after.png"});
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
