const { chromium } = require("playwright");
(async()=>{
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN"});
  const p = await c.newPage();
  await p.goto("https://www.namecheap.com/affiliates/",{waitUntil:"domcontentloaded",timeout:45000});
  await p.waitForTimeout(2000);
  const info = await p.evaluate(()=>{
    const main = document.querySelector("main") || document.body;
    const links = [...main.querySelectorAll("a")].map(a=>({t:(a.innerText||"").trim().slice(0,60), h:a.href}));
    return links.slice(0,60);
  });
  for (const l of info) console.log(l.t.replace(/\n/g," ") || "(no text)", "->", l.h);
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
