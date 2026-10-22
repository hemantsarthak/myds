const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
const gql = async (p, query, variables) => p.evaluate(async ({query, variables}) => {
  const r = await fetch("/api/graphql",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query, variables})});
  return await r.text();
}, {query, variables});
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(2500);
  const srcOut = await gql(p, `query { currentPartner { sources { id name channelType sourceType approved } } }`);
  console.log("SOURCES:", srcOut.slice(0,800));
  let sid = null;
  try { const j = JSON.parse(srcOut); const ss = j.data?.currentPartner?.sources || []; if (ss.length) sid = ss[0].id; } catch(e){}
  const MUT = `mutation CPL($input: CreatePartnerLinkInput!) { createPartnerLink(input: $input) { errors partnerLink { id url fullUrl shortUrl brandId status name } } }`;
  const attempts = [
    { sourceId: sid, brandId: "84", url: "https://www.booking.com/", name: "Airport hotels" },
    { sourceId: sid, brandId: 84, url: "https://www.booking.com/" },
    { brandId: 84, url: "https://www.booking.com/" },
  ];
  for (const inp of attempts) {
    console.log("TRY", JSON.stringify(inp));
    console.log("  ->", (await gql(p, MUT, {input: inp})).slice(0,700));
  }
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
