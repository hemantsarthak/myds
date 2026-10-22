const { chromium } = require("playwright");
(async()=>{
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN"});
  const p = await c.newPage();
  await p.goto("https://www.namecheap.com/affiliates/",{waitUntil:"domcontentloaded",timeout:45000});
  await p.waitForTimeout(2500);
  const links = await p.$$eval("a", as => as.map(a=>({t:(a.innerText||"").trim().slice(0,40), h:a.href})).filter(x=>/apply|affiliate|sign ?up|register|impact|cj|shareasale|partner/i.test(x.t+" "+x.h)));
  console.log(JSON.stringify(links,null,1).slice(0,3000));
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
