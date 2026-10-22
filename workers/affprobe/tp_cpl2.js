const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
const gql = async (p, query, variables) => p.evaluate(async ({query, variables}) => {
  const r = await fetch("/api/graphql",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query, variables})});
  return await r.text();
}, {query, variables});
const MUT = `mutation CPL($input: CreatePartnerLinkInput!) { createPartnerLink(input: $input) { errors partnerLink { id url fullUrl shortUrl status name } } }`;
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(2500);
  const urls = ["https://www.booking.com/","https://aviasales.com/","https://airhelp.com/","https://www.klook.com/","https://nordvpn.com/"];
  for (const u of urls) {
    const out = await gql(p, MUT, {input: {sourceId: "589091", url: u}});
    console.log(u, "->", out.slice(0,420));
  }
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
