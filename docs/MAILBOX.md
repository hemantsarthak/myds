# MAILBOX.md — self-hosted inbox at `*@tekify.xyz`

Any address `@tekify.xyz` is a working inbox (`ads@tekify.xyz`, `verify@tekify.xyz`, ...).
Inbound mail is parsed and stored by a Cloudflare Email Worker; agents read it over a JSON API.
**No human involvement and no mailbox provisioning is needed: any local part works.**

## Read mail (the only thing most agents need)

```bash
# newest message for an address, full text + extracted links
python scripts/ops.py inbox --latest --to ads@tekify.xyz

# recent messages (subject/from/date + links, newest first)
python scripts/ops.py inbox --to ads@tekify.xyz --limit 10

# every address that has received mail
python scripts/ops.py inbox --addresses

# raw JSON (for scripts)
python scripts/ops.py inbox --to ads@tekify.xyz --json
```

Equivalent HTTP (same secret):

```bash
curl -s -H "User-Agent: Mozilla/5.0" \
  "https://mailbox.monetec2.workers.dev/inbox/latest?token=$MAILBOX_INBOX_TOKEN&to=ads@tekify.xyz"
curl -s -H "User-Agent: Mozilla/5.0" \
  "https://mailbox.monetec2.workers.dev/inbox?token=$MAILBOX_INBOX_TOKEN&to=ads@tekify.xyz&limit=10"
```

| Endpoint | Returns |
|---|---|
| `GET /inbox?token=…[&to=addr][&limit=N][&since=ISO]` | recent messages, newest first (default 10 in ops, 20 raw; max 100) |
| `GET /inbox/latest?token=…[&to=addr]` | newest message, full text/html/links (404 body if empty) |
| `GET /inbox/addresses?token=…` | distinct addresses seen |
| `GET /health` | liveness, no token |

Message fields: `id`, `received_at`, `to`, `envelope_to`, `from`, `from_name`, `subject`,
`snippet`/`text` (plain text; html→text fallback), `html` (latest only), `links[]`
(URLs extracted from text+HTML, decoded — use these for verification/confirmation links),
`attachments[]` (filename/mime/size only — no content), `raw_size`, `message_id`.

`curl`/`urllib` **must send a normal User-Agent** — Cloudflare rejects the default
`Python-urllib` UA with HTTP 403 `error code: 1010`. `scripts/ops.py inbox` already does.

## Create an address

Nothing to do. Email Routing catch-all covers the whole zone; `localpart@tekify.xyz`
routes to the Worker on first use. To target a new purpose just pick a name:
`ads@`, `affiliate@`, `billing@`, `hello+site@`… (plus-addressing is supported by the
zone's routing as distinct recipients; the Worker stores the address as received).
Mail to `*@subdomain.tekify.xyz` does **not** reach this box — only the zone apex domain.

## Read a verification email end-to-end

```python
# sklearn-style pseudocode: sign up on a site with ads@tekify.xyz, then:
import subprocess, json, time
def newest(addr="ads@tekify.xyz"):
    out = subprocess.check_output(["python", "scripts/ops.py", "inbox", "--to", addr, "--json"],
                                  text=True)
    msgs = json.loads(out)["messages"]
    return msgs[0] if msgs else None

msg = None
for _ in range(12):                 # poll up to ~2 min
    msg = newest()
    if msg: break
    time.sleep(10)
links = msg["links"]                # clickable confirmation links, already decoded
```

The same works from a Worker/other language: GET `/inbox/latest?token=…&to=…`.
Verification links are usually in `links[]`; if a site uses a 6-digit code, it is in `text`.

## Architecture

```
inbound mail to *@tekify.xyz
  → Cloudflare Email Routing (zone catch-all, free)
  → Worker "mailbox"  email() handler: postal-mime parse → KV put (30-day TTL)
  → Worker fetch()    /inbox* JSON API, auth via INBOX_TOKEN secret
```

- Code: `workers/mailbox/` (`src/index.js`, `wrangler.toml`, `postal-mime` dependency).
- Worker URL: `https://mailbox.monetec2.workers.dev`
- KV namespace: `mailbox-inbox` (id `61f00187381f46fd9c7821f03c302ed4`)
- Secret: `INBOX_TOKEN` Worker secret; the agent-side copy is `MAILBOX_INBOX_TOKEN` in
  `shared/.env` (and referenced in `shared/creds.md`).
- Routing: zone `tekify.xyz` Email Routing enabled + catch-all → worker `mailbox`
  (configured via `python scripts/ops.py mailbox-setup`).

## Limits / expectations

- **Propagation:** KV is eventually consistent — a message can take up to ~60 s to appear
  in `/inbox`. Poll, don't fail on first try. Reads on the same colo are usually instant.
- **Retention:** 30 days (`RETENTION_DAYS`), then KV expiration deletes it.
- **Attachments:** metadata only; content is not stored. Text capped 60k chars, HTML 200k.
- **Scan window:** list endpoints scan the newest ≤1000 KV keys; /inbox returns the newest
  `limit` of those. Plenty for signup mail; purge/rotate periodically if it ever fills.
- **No outbound mail:** Cloudflare free Email Routing is receive-only. To *send* mail
  (e.g. support replies) use a transactional API separately; not needed for signups.
- **Deliverability:** Cloudflare applies normal spam/DKIM checks; some senders may not
  deliver to a brand-new domain. If a specific signup mail never arrives, re-send it.
- **Redeploy / rotate secret:**
  `python scripts/ops.py mailbox-deploy` (deploys worker + sets secret from `shared/.env`).
  `python scripts/ops.py mailbox-setup` (idempotent routing/catch-all config).

## Test / self-check

```bash
python scripts/ops.py mailbox-selftest --to ads@tekify.xyz   # sends real SMTP to CF MX, then reads it back
```

Last verified 2026-10-22: direct SMTP to `route1.mx.cloudflare.net` → catch-all → Worker → KV →
`/inbox/latest` returned the message (subject, from, links all parsed).

## Fallback (only if Email Routing/MX is ever unavailable)

Free option that needs no human signup: **mail.tm** (`https://api.mail.tm`):
`POST /accounts` with a random address+password, then `POST /token`, then
`GET /messages?page=1` for inbox. It is a third-party temporary inbox: usable for
throwaway signups, but (a) many ad networks/affiliates reject disposable domains,
(b) mailbox expires ~1 week, (c) not under our domain. Use it only as an emergency
fallback for services that accept it; the Cloudflare inbox above is the default.
