const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
const gql = async (p, query, variables) => p.evaluate(async ({query, variables}) => {
  const r = await fetch("/api/graphql",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query, variables})});
  return await r.text();
}, {query, variables});
const MUT = `mutation CPL($input: CreatePartnerLinkInput!) { createPartnerLink(input: $input) { errors partnerLink { id url fullUrl shortUrl status } } }`;
const targets = {
 "84":"https://www.booking.com/index.html", "84b":"https://www.booking.com/hotels/",
 "121":"https://www.trip.com/", "111":"https://www.kiwi.com/",
 "637":"https://www.hotels.com/", "104":"https://www.agoda.com/",
 "594":"https://www.expedia.com/", "108":"https://www.getyourguide.com/",
 "47":"https://www.viator.com/", "117":"https://www.discovercars.com/",
 "541":"https://www.airalo.com/", "629":"https://saily.com/",
 "224":"https://yesim.tech/", "93":"https://www.hostelworld.com/",
 "209":"https://radicalstorage.com/", "180":"https://www.prioritypass.com/",
 "91":"https://www.omio.com/", "44":"https://12go.asia/",
 "86":"https://compensair.com/", "89":"https://www.tiqets.com/",
 "627":"https://www.welcomepickups.com/", "147":"https://www.gettransfer.com/",
 "633":"https://www.kkday.com/", "638":"https://www.vio.com/",
 "10":"https://www.economybookings.com/", "172":"https://www.qeeq.com/",
 "631":"https://nordvpn.com/pricing", "982":"https://www.tripadvisor.com/",
};
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(2000);
  const res = {};
  for (const [k,u] of Object.entries(targets)) {
    const out = await gql(p, MUT, {input: {sourceId: "589091", url: u}});
    try {
      const pl = JSON.parse(out).data.createPartnerLink.partnerLink;
      res[k] = {url: u, status: pl.status, fullUrl: pl.fullUrl, shortUrl: pl.shortUrl, id: pl.id};
      console.log(k.padEnd(5), pl.status, (pl.shortUrl||pl.fullUrl||"").slice(0,110));
    } catch(e){ console.log(k, "ERR", out.slice(0,150)); res[k]={url:u,status:"ERROR",raw:out.slice(0,200)}; }
  }
  fs.writeFileSync(path.join(SHARED,"travelpayouts_links.json"), JSON.stringify(res,null,1));
  console.log("saved shared/travelpayouts_links.json");
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
