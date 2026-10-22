/**
 * tekify-analytics — cookie-free, self-hosted pageview counter.
 *
 * Public:
 *   GET /e.js?site=<slug>   tiny beacon script (one hit per pageview, no cookies, no CORS)
 *   GET /hit?site&p&r&t     records one pageview, answers with a 1x1 gif
 * Protected (token = ANALYTICS_TOKEN secret):
 *   GET /stats?token&site=<slug>[&day=YYYY-MM-DD][&days=N][&top=N]
 *   GET /stats/all?token
 *
 * Storage design (Workers KV free tier is only 1k writes/day!):
 *   Hits are aggregated in isolate memory, then flushed as ONE immutable "shard" key
 *   per site/day:  s:<site>:<day>:<flush-ms>:<rand>   ->  {views,bots,paths,refs}
 *   Stats sum shards (metadata for totals, values for top lists). No read-modify-write,
 *   so concurrent isolates can never overwrite each other's counts.
 *
 *   Flush triggers (each flush = 1 KV write):
 *     - first hit on a cold isolate                     (persists immediately)
 *     - FLUSH_HITS (50) hits buffered                   (busy traffic)
 *     - a deferred ~20 s ctx.waitUntil() flush          (captures the rest of a visit;
 *       nb: plain module-level setTimeout does NOT run after the response in Workers)
 *     - any hit ≥ FLUSH_MS (5 min) after the last flush (low-traffic safety net)
 *     - every /stats request flushes pending hits first (stats are current)
 *   Tradeoff: hits still buffered when the isolate is evicted are lost; the 600/day
 *   write cap protects the account's 1k/day KV budget at high traffic.
 */

const GIF = Uint8Array.from(
  atob("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
  (c) => c.charCodeAt(0)
);

const SLUG_RE = /^[a-z0-9][a-z0-9-]{0,63}$/;
const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;
const BOT_RE =
  /bot|crawl|spider|slurp|headless|phantom|preview|monitor|uptime|curl|wget|python-requests|python-urllib|httpclient|go-http|java\/|axios|node-fetch|facebookexternalhit|bingpreview|scanner|probe|okhttp|libwww|ahrefs|semrush/i;

const MAX_PATHS = 200; // distinct paths per shard (overflow -> "(other)")
const MAX_REFS = 100; // distinct referrer hosts per shard (overflow -> "(other)")
const MAX_SCAN_KEYS = 5000; // per stats query safety cap on shards read

// ---------------------------------------------------------------- tuning
// Configurable via [vars] in wrangler.toml / env (non-secret):
//   FLUSH_HITS=50  FLUSH_MS=300000  DEFER_MS=20000  RETENTION_DAYS=90  MAX_FLUSH_PER_DAY=600
function cfg(env) {
  return {
    flushHits: Math.max(1, Number(env.FLUSH_HITS || 50)),
    flushMs: Math.max(1000, Number(env.FLUSH_MS || 300_000)),
    deferMs: Math.min(Math.max(1000, Number(env.DEFER_MS || 20_000)), 25_000),
    retentionDays: Math.max(1, Number(env.RETENTION_DAYS || 90)),
  };
}

// ---------------------------------------------------------------- state
const buf = new Map(); // "site|day" -> shard entry awaiting flush
let pendingHits = 0;
let lastFlushAt = 0;
let flushing = false;
let deferred = false; // a ctx.waitUntil delayed flush is already scheduled
let writeDay = "";
let writesToday = 0;

// ---------------------------------------------------------------- helpers
function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2) + "\n", {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
}

function gif() {
  return new Response(GIF, {
    headers: {
      "content-type": "image/gif",
      "cache-control": "no-store, no-cache, must-revalidate, max-age=0",
      "access-control-allow-origin": "*",
    },
  });
}

function js(body) {
  return new Response(body, {
    headers: {
      "content-type": "application/javascript; charset=utf-8",
      "cache-control": "public, max-age=3600",
      "x-content-type-options": "nosniff",
    },
  });
}

function tokenOk(provided, env) {
  const expected = env.ANALYTICS_TOKEN;
  if (!expected || !provided || provided.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= provided.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

function utcDay(ms = Date.now()) {
  return new Date(ms).toISOString().slice(0, 10);
}

function addDays(day, n) {
  const t = Date.parse(day + "T00:00:00Z") + n * 86_400_000;
  return new Date(t).toISOString().slice(0, 10);
}

function cleanSlug(raw) {
  const s = String(raw || "").trim().toLowerCase();
  return SLUG_RE.test(s) ? s : "";
}

function cleanPath(raw) {
  let p = String(raw || "/").split("?")[0].split("#")[0];
  p = p.replace(/[\u0000-\u001f]/g, "").slice(0, 300);
  if (!p.startsWith("/")) p = "/" + p;
  return p || "/";
}

function cleanRef(raw) {
  let r = String(raw || "").trim().toLowerCase().replace(/:\d+$/, "").split("/")[0];
  r = r.replace(/[^a-z0-9.-]/g, "").replace(/^www\./, "").slice(0, 120);
  return r;
}

function rand() {
  return (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36)).replace(/-/g, "").slice(0, 10);
}

// ---------------------------------------------------------------- counting
function addCount(obj, key, cap) {
  if (key in obj) obj[key]++;
  else if (Object.keys(obj).length >= cap) obj["(other)"] = (obj["(other)"] || 0) + 1;
  else obj[key] = 1;
}

function recordHit(env, ctx, { site, path, ref, ua }) {
  const now = Date.now();
  const day = utcDay(now);
  const key = site + "|" + day;
  let e = buf.get(key);
  if (!e) {
    e = { site, day, views: 0, bots: 0, paths: {}, refs: {}, created: new Date(now).toISOString() };
    buf.set(key, e);
  }
  const isBot = !ua || BOT_RE.test(ua);
  if (isBot) {
    e.bots++;
  } else {
    e.views++;
    addCount(e.paths, path, MAX_PATHS);
    if (ref) addCount(e.refs, ref, MAX_REFS);
  }
  pendingHits++;

  const c = cfg(env);
  const cold = lastFlushAt === 0;
  const stale = !cold && now - lastFlushAt >= c.flushMs;
  if (cold || pendingHits >= c.flushHits || stale) {
    // Cold isolate / busy traffic / stale buffer: persist now. Advance the clock
    // synchronously so a burst of first requests cannot stampede one write each.
    lastFlushAt = now;
    ctx.waitUntil(flush(env));
  } else {
    scheduleDeferredFlush(env, ctx, c.deferMs);
  }
}

/** Capture the tail of a visit: one ctx.waitUntil flush ~DEFER_MS after a hit.
 *  (A plain module-level setTimeout does NOT run after the response in Workers.) */
function scheduleDeferredFlush(env, ctx, delayMs) {
  if (deferred) return;
  deferred = true;
  const wait = new Promise((resolve) => setTimeout(resolve, delayMs));
  ctx.waitUntil(
    wait
      .then(() => {
        deferred = false;
        return flush(env);
      })
      .catch((err) => {
        deferred = false;
        console.log("deferred flush failed", err && err.message);
      })
  );
}

/** Write every buffered shard as its own immutable KV key (one write per shard). */
async function flush(env) {
  if (flushing || buf.size === 0) return { flushed: 0 };
  const today = utcDay();
  if (today !== writeDay) {
    writeDay = today;
    writesToday = 0;
  }
  const cap = Number(env.MAX_FLUSH_PER_DAY || 600);
  if (writesToday >= cap) {
    console.log(`flush deferred: ${writesToday} writes already used today`);
    return { flushed: 0, deferred: true };
  }
  flushing = true;
  const entries = [...buf.entries()];
  buf.clear();
  pendingHits = 0;
  lastFlushAt = Date.now();
  const stamp = String(lastFlushAt).padStart(13, "0");
  const retentionTtl = cfg(env).retentionDays * 86_400;
  try {
    await Promise.all(
      entries.map(([key, e]) => {
        const kvKey = `s:${e.site}:${e.day}:${stamp}:${rand()}`;
        return env.ANALYTICS.put(kvKey, JSON.stringify(e), {
          expirationTtl: retentionTtl,
          metadata: { site: e.site, day: e.day, views: e.views, bots: e.bots },
        });
      })
    );
    writesToday += entries.length;
    console.log(`flushed ${entries.length} shard(s), writesToday=${writesToday}`);
    return { flushed: entries.length };
  } catch (err) {
    console.log("flush failed", err && err.message);
    return { flushed: 0, error: String(err && err.message) };
  } finally {
    flushing = false;
  }
}

// ---------------------------------------------------------------- stats read
async function listKeys(env, prefix, cap = MAX_SCAN_KEYS) {
  const keys = [];
  let cursor;
  do {
    const page = await env.ANALYTICS.list({ prefix, limit: 1000, cursor });
    for (const k of page.keys) keys.push({ name: k.name, metadata: k.metadata || null });
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor && keys.length < cap);
  return keys.slice(0, cap);
}

async function sumShards(env, site, days, withTop, topN) {
  const perDay = [];
  const totals = { views: 0, bots: 0 };
  const paths = {};
  const refs = {};
  let shards = 0;
  for (const day of days) {
    const keys = await listKeys(env, `s:${site}:${day}:`);
    shards += keys.length;
    const dayTotals = { views: 0, bots: 0 };
    for (const k of keys) {
      if (k.metadata) {
        dayTotals.views += Number(k.metadata.views || 0);
        dayTotals.bots += Number(k.metadata.bots || 0);
      }
    }
    if (withTop && keys.length) {
      const values = await Promise.all(
        keys.map((k) => env.ANALYTICS.get(k.name, "json").catch(() => null))
      );
      for (const v of values) {
        if (!v) continue;
        for (const [p, n] of Object.entries(v.paths || {})) paths[p] = (paths[p] || 0) + n;
        for (const [r, n] of Object.entries(v.refs || {})) refs[r] = (refs[r] || 0) + n;
      }
    }
    totals.views += dayTotals.views;
    totals.bots += dayTotals.bots;
    perDay.push({ day, views: dayTotals.views, bots: dayTotals.bots, shards: keys.length });
  }
  const top = (obj) =>
    Object.entries(obj)
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, topN)
      .map(([key, views]) => ({ key, views }));
  return {
    totals,
    perDay,
    shards,
    top_pages: top(paths).map((x) => ({ path: x.key, views: x.views })),
    top_referrers: top(refs).map((x) => ({ referrer: x.key === "(other)" ? "(other)" : x.key, views: x.views })),
    distinct_paths: Object.keys(paths).length,
    distinct_referrers: Object.keys(refs).length,
  };
}

async function handleStats(url, env) {
  await flush(env); // persist any in-memory hits first so stats are current
  const site = cleanSlug(url.searchParams.get("site"));
  if (!site) return json({ ok: false, error: "bad or missing site slug" }, 400);
  const daysN = Math.min(Math.max(parseInt(url.searchParams.get("days") || "1", 10) || 1, 1), 90);
  const endDay = url.searchParams.get("day") || utcDay();
  if (!DAY_RE.test(endDay)) return json({ ok: false, error: "day must be YYYY-MM-DD" }, 400);
  const topN = Math.min(Math.max(parseInt(url.searchParams.get("top") ?? "20", 10) || 0, 0), 100);
  const days = [];
  for (let i = daysN - 1; i >= 0; i--) days.push(addDays(endDay, -i));

  const data = await sumShards(env, site, days, topN > 0, topN);
  return json({
    ok: true,
    site,
    range: { from: days[0], to: days[days.length - 1] },
    days: data.perDay,
    totals: data.totals,
    top_pages: data.top_pages,
    top_referrers: data.top_referrers,
    distinct_paths: data.distinct_paths,
    distinct_referrers: data.distinct_referrers,
    shards: data.shards,
    generated_at: new Date().toISOString(),
  });
}

async function handleStatsAll(url, env) {
  await flush(env);
  const keys = await listKeys(env, "s:", 10_000);
  const sites = new Map();
  for (const k of keys) {
    const parts = k.name.split(":");
    if (parts.length < 3) continue;
    const site = parts[1];
    const day = parts[2];
    let s = sites.get(site);
    if (!s) {
      s = { site, shards: 0, days: new Set(), first_day: day, last_day: day, views: 0, bots: 0 };
      sites.set(site, s);
    }
    s.shards++;
    s.days.add(day);
    if (day < s.first_day) s.first_day = day;
    if (day > s.last_day) s.last_day = day;
    if (k.metadata) {
      s.views += Number(k.metadata.views || 0);
      s.bots += Number(k.metadata.bots || 0);
    }
  }
  const out = [...sites.values()]
    .map((s) => ({ ...s, days: s.days.size }))
    .sort((a, b) => b.views - a.views || a.site.localeCompare(b.site));
  return json({ ok: true, sites: out, total_shards: keys.length, generated_at: new Date().toISOString() });
}

// ---------------------------------------------------------------- e.js
function ejs(request, env, site) {
  const origin = new URL(request.url).origin;
  const internal = String(env.INTERNAL_DOMAIN || "tekify.xyz").toLowerCase();
  // Deliberately tiny, no cookies, no CORS, one beacon per pageview.
  return (
    "(function(){var s=" + JSON.stringify(site) + ",b=" + JSON.stringify(origin) +
    ",i=" + JSON.stringify(internal) + ";function h(){var p=\"/\",r=\"\",t=\"\";" +
    "try{p=location.pathname||\"/\"}catch(e){}" +
    "try{var u=document.referrer;if(u){var a=document.createElement(\"a\");a.href=u;r=a.hostname||\"\"}}catch(e){}" +
    "try{t=document.title||\"\"}catch(e){}" +
    "if(r){r=r.toLowerCase();if(r===i||r.slice(-(i.length+1))===\".\"+i)r=\"\"}" +
    "var q=b+\"/hit?site=\"+encodeURIComponent(s)+\"&p=\"+encodeURIComponent(p.slice(0,300))+" +
    "\"&r=\"+encodeURIComponent(r.slice(0,120))+\"&t=\"+encodeURIComponent(t.slice(0,200))+" +
    "\"&n=\"+Math.random().toString(36).slice(2,10);" +
    "try{var img=new Image();img.src=q}catch(e){}}h()})();"
  );
}

// ---------------------------------------------------------------- fetch API
async function handleFetch(request, env, ctx) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/\/+$/, "") || "/";

  if (path === "/" || path === "/health") {
    return json({ ok: true, service: "tekify-analytics", time: new Date().toISOString() });
  }
  if (path === "/e.js") {
    const site = cleanSlug(url.searchParams.get("site"));
    if (!site) return new Response("// bad site\n", { status: 400, headers: { "content-type": "application/javascript" } });
    return js(ejs(request, env, site));
  }
  if (path === "/hit") {
    const site = cleanSlug(url.searchParams.get("site"));
    if (site) {
      recordHit(env, ctx, {
        site,
        path: cleanPath(url.searchParams.get("p")),
        ref: cleanRef(url.searchParams.get("r")),
        ua: request.headers.get("user-agent") || "",
      });
    }
    return gif();
  }
  if (!tokenOk(url.searchParams.get("token"), env)) {
    return json({ ok: false, error: "unauthorized: missing or bad token" }, 401);
  }
  try {
    if (path === "/stats") return await handleStats(url, env);
    if (path === "/stats/all") return await handleStatsAll(url, env);
    return json({ ok: false, error: `not found: ${path}` }, 404);
  } catch (err) {
    console.log("stats failed", err && err.stack);
    return json({ ok: false, error: String((err && err.message) || err) }, 500);
  }
}

export default {
  fetch(request, env, ctx) {
    return handleFetch(request, env, ctx);
  },
};
