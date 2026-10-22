/**
 * tekify-mailbox — self-hosted inbox at *@tekify.xyz
 *
 *   email()  : Cloudflare Email Worker. Every inbound message (catch-all) is
 *              parsed and stored durably in the INBOX KV namespace for 30 days.
 *   fetch()  : JSON read API used by agents to poll for verification emails.
 *
 *   GET /health?                        -> { ok: true }            (public)
 *   GET /inbox?token=X[&to=a@tekify.xyz][&limit=20][&since=ISO]
 *   GET /inbox/latest?token=X[&to=a@tekify.xyz]
 *   GET /inbox/addresses?token=X        -> distinct addresses seen
 *
 * Every read endpoint requires the INBOX_TOKEN secret. See docs/MAILBOX.md.
 */

import PostalMime from "postal-mime";

const MAX_TEXT = 60_000;        // chars of plain text kept per message
const MAX_HTML = 200_000;       // chars of html kept per message
const MAX_LIST = 1000;          // newest N KV keys scanned per query
const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 20;
const MSG_PREFIX = "msg:";

// ------------------------------------------------------------------ helpers
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

function addr(s) {
  return String(s || "").trim().toLowerCase();
}

function trunc(s, n) {
  s = String(s || "");
  return s.length > n ? s.slice(0, n) : s;
}

/** strip HTML tags to readable text (fallback when a mail has no text/plain part) */
function htmlToText(html) {
  return String(html || "")
    .replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|div|h[1-6]|li|tr)>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#(\d+);/g, (_, d) => String.fromCharCode(Number(d)))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCharCode(parseInt(h, 16)))
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function extractLinks(text, html) {
  const found = new Set();
  const re = /https?:\/\/[^\s"'<>()[\]\\]+/gi;
  for (const src of [text, html]) {
    if (!src) continue;
    let m;
    while ((m = re.exec(src))) {
      // HTML entities inside hrefs are common; decode the basics.
      const url = m[0]
        .replace(/&amp;/g, "&")
        .replace(/[.,;:!?)\]}>]+$/, "");
      if (url.length > 10) found.add(url);
    }
  }
  return [...found].slice(0, 30);
}

function keyTimestamp(ms) {
  return String(ms).padStart(13, "0"); // fixed width => lexicographic == chronological
}

function tokenOk(provided, env) {
  const expected = env.INBOX_TOKEN;
  if (!expected || !provided) return false;
  // constant-time-ish compare
  if (provided.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= provided.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

function publicMessage(rec, { full = false } = {}) {
  const base = {
    id: rec.id,
    received_at: rec.received_at,
    to: rec.to,
    from: rec.from,
    from_name: rec.from_name,
    subject: rec.subject,
    snippet: trunc(rec.text, 300),
    text_length: (rec.text || "").length,
    links: rec.links || [],
    attachments: rec.attachments || [],
  };
  base.text = full ? rec.text : trunc(rec.text, 2000);
  if (full && rec.html) base.html = rec.html;
  return base;
}

// ------------------------------------------------------------- storage (email)
async function storeMessage(message, env) {
  const receivedAt = new Date();
  const envelopeTo = addr(message.to);
  const raw = await new Response(message.raw).text();

  let parsed = null;
  try {
    parsed = await PostalMime.parse(raw);
  } catch (e) {
    console.log(`postal-mime parse failed for ${envelopeTo}: ${e?.message || e}`);
  }

  const fromObj = parsed?.from || (message.from ? { address: message.from } : null);
  const subject = parsed?.subject || "(no subject)";
  const html = trunc(parsed?.html, MAX_HTML);
  let text = trunc(parsed?.text, MAX_TEXT);
  if (!text && html) text = trunc(htmlToText(html), MAX_TEXT);

  const toList = (parsed?.to || [])
    .map((t) => addr(t.address))
    .filter(Boolean);
  if (!toList.length && envelopeTo) toList.push(envelopeTo);

  const attachments = (parsed?.attachments || []).map((a) => ({
    filename: a.filename || "",
    mime_type: a.mimeType || "",
    size: a.content?.byteLength ?? a.content?.length ?? 0,
  }));

  const id = crypto.randomUUID();
  const rec = {
    id,
    received_at: receivedAt.toISOString(),
    received_ms: receivedAt.getTime(),
    to: toList.join(", "),
    envelope_to: envelopeTo,
    from: addr(fromObj?.address) || addr(message.from),
    from_name: fromObj?.name || "",
    subject,
    text,
    html,
    links: extractLinks(text, html),
    attachments,
    raw_size: raw.length,
    message_id: parsed?.messageId || "",
    headers: pickHeaders(parsed?.headers),
  };

  const key = `${MSG_PREFIX}${envelopeTo}:${keyTimestamp(rec.received_ms)}:${id}`;
  await env.INBOX.put(key, JSON.stringify(rec), {
    // KV metadata is capped at 1024 bytes; keep it small for listing.
    metadata: {
      from: trunc(rec.from, 100),
      subject: trunc(rec.subject, 150),
      received_at: rec.received_at,
    },
    expirationTtl: 60 * 60 * 24 * Number(env.RETENTION_DAYS || 30),
  });
  return { key, rec };
}

function pickHeaders(headers) {
  const wanted = [
    "reply-to", "date", "message-id", "return-path", "list-unsubscribe",
    "x-mailer", "authentication-results", "dkim-signature",
  ];
  const out = {};
  for (const h of headers || []) {
    if (wanted.includes(String(h.key || "").toLowerCase())) out[h.key] = h.value;
  }
  return out;
}

async function handleEmail(message, env) {
  const { key, rec } = await storeMessage(message, env);
  console.log(
    `stored ${key} from=${rec.from} subject=${JSON.stringify(trunc(rec.subject, 80))} bytes=${rec.raw_size}`
  );
}

// ------------------------------------------------------------------ read API
async function listKeys(env, prefix, limit) {
  const res = await env.INBOX.list({ prefix, limit: Math.min(Math.max(limit, 1), MAX_LIST) });
  return res.keys.map((k) => k.name);
}

async function getRecords(env, keys) {
  const recs = await Promise.all(keys.map((k) => env.INBOX.get(k, "json")));
  return recs; // KV reads are fast; Promise.all keeps this within a request
}

async function handleInbox(url, env) {
  const to = addr(url.searchParams.get("to"));
  const limit = Math.min(
    Math.max(parseInt(url.searchParams.get("limit") || DEFAULT_LIMIT, 10) || DEFAULT_LIMIT, 1),
    MAX_LIMIT
  );
  const since = url.searchParams.get("since"); // ISO date-time; optional

  const prefix = to ? `${MSG_PREFIX}${to}:` : MSG_PREFIX;
  const keys = await listKeys(env, prefix, MAX_LIST);
  if (!keys.length) {
    return json({ ok: true, address: to || "*", count: 0, messages: [] });
  }

  // Newest-first, but only fetch `limit` bodies.
  keys.sort();
  const newest = keys.slice(-limit).reverse();
  const records = await getRecords(env, newest);

  let messages = records.filter(Boolean).map((r) => publicMessage(r));
  if (since) {
    const t = Date.parse(since);
    if (!Number.isNaN(t)) messages = messages.filter((m) => Date.parse(m.received_at) >= t);
  }
  return json({ ok: true, address: to || "*", count: messages.length, messages });
}

async function handleLatest(url, env) {
  const to = addr(url.searchParams.get("to"));
  const prefix = to ? `${MSG_PREFIX}${to}:` : MSG_PREFIX;
  const keys = await listKeys(env, prefix, MAX_LIST);
  if (!keys.length) return json({ ok: true, address: to || "*", message: null }, 404);
  keys.sort();
  const rec = await env.INBOX.get(keys[keys.length - 1], "json");
  if (!rec) return json({ ok: true, address: to || "*", message: null }, 404);
  return json({ ok: true, address: to || "*", message: publicMessage(rec, { full: true }) });
}

async function handleAddresses(env) {
  const keys = await listKeys(env, MSG_PREFIX, MAX_LIST);
  const seen = new Set();
  for (const k of keys) {
    // key = msg:<address>:<13-digit-ts>:<uuid>; addresses contain no ':'
    const parts = k.slice(MSG_PREFIX.length).split(":");
    if (parts.length >= 3) seen.add(parts[0]);
  }
  return json({ ok: true, count: seen.size, addresses: [...seen].sort() });
}

// ------------------------------------------------------------------ fetch API
async function handleFetch(request, env) {
  const url = new URL(request.url);
  if (request.method !== "GET" && request.method !== "HEAD") {
    return json({ ok: false, error: "method not allowed" }, 405);
  }
  if (url.pathname === "/" || url.pathname === "/health") {
    return json({ ok: true, service: "tekify-mailbox", domain: env.MAIL_DOMAIN || "tekify.xyz" });
  }
  if (!tokenOk(url.searchParams.get("token"), env)) {
    return json({ ok: false, error: "unauthorized: missing or bad token" }, 401);
  }
  try {
    if (url.pathname === "/inbox") return await handleInbox(url, env);
    if (url.pathname === "/inbox/latest") return await handleLatest(url, env);
    if (url.pathname === "/inbox/addresses") return await handleAddresses(env);
    return json({ ok: false, error: `not found: ${url.pathname}` }, 404);
  } catch (e) {
    console.log(`fetch error: ${e?.stack || e}`);
    return json({ ok: false, error: String(e?.message || e) }, 500);
  }
}

export default {
  async email(message, env, ctx) {
    // Catch-all routing sends everything here; reject nothing that we can store.
    try {
      await handleEmail(message, env);
    } catch (e) {
      console.log(`email handler failed: ${e?.stack || e}`);
      throw e; // let Cloudflare report a delivery failure rather than silently drop
    }
  },

  fetch(request, env, ctx) {
    return handleFetch(request, env, ctx);
  },
};
