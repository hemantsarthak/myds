"""engine/ads.py — the ONE place ad network snippets live.

Status (2026-10-22): LIVE — HilltopAds publisher account created and verified
autonomously (no human KYC). Account 409868, website `tekify.xyz` (siteId 925719,
domain verified by DNS TXT; site approval pending manual moderation while the ad
zones themselves are already Approved/Active). See docs/ADS.md for the full record.

Placement policy (from docs/STRATEGY.md):
  - 2 in-page units max: in-page push (slot 1) + 300x250 banner (slot 2)
  - 1 optional popunder (head, below); remove the POPUNDER block to disable
  - no interstitials, no adult ads, script loads are async and do not block render

Every snippet below is the EXACT invocation code from the HilltopAds dashboard
(only `\\/` was normalised to `/`); do not hand-edit the URLs.
"""

MONETIZATION_ON = True


# ---------------------------------------------------------------------------
# Popunder (optional, site-wide). Zone #7541169 (Popunder, APPROVED).
# To disable popunder without touching the slots, set POPUNDER = "".
# ---------------------------------------------------------------------------
POPUNDER = """
<script>
(function(rkqi){
var d = document,
    s = d.createElement('script'),
    l = d.currentScript || d.scripts[d.scripts.length - 1];
s.settings = rkqi || {};
s.src = "//subtle-injury.com/c.D/9b6Bb/2U5dltS/WtQ/9iNmzxUH0RMbTYEj2sO_Sn0/3MN/T_Q/xKMMTmcxzR";
s.async = true;
s.referrerPolicy = 'no-referrer-when-downgrade';
l.parentNode.insertBefore(s, l);
})({})
</script>
"""

# ---------------------------------------------------------------------------
# Slot 1 — In-Page Push, zone #7541137 (MultiTag in-page push, APPROVED).
# Non-intrusive bottom-right notification-style native ads, ideal for content sites.
# ---------------------------------------------------------------------------
INPAGE_PUSH = """
<script>
(function(snzqs){
var d = document,
    s = d.createElement('script'),
    l = d.currentScript || d.scripts[d.scripts.length - 1];
s.settings = snzqs || {};
s.src = "//unfoldedtrade.com/bqXuV.s/dGGFl/0hY-WqcQ/ne-m/9bulZXUpl/kJPyTAcw1AN/DPEoxCMsz/cltYNlz/Uo0bMwTJEY0MMFQS";
s.async = true;
s.referrerPolicy = 'no-referrer-when-downgrade';
l.parentNode.insertBefore(s, l);
})({})
</script>
"""

# ---------------------------------------------------------------------------
# Slot 2 — MultiTag Banner 300x250, zone #7541153 (APPROVED).
# Self-inserting banner; place inside the article body.
# ---------------------------------------------------------------------------
BANNER_300x250 = """
<script>
(function(lmicm){
var d = document,
    s = d.createElement('script'),
    l = d.currentScript || d.scripts[d.scripts.length - 1];
s.settings = lmicm || {};
s.src = "//unfoldedtrade.com/b.XdVQsbdqGFlz0ZY_Wdca/Yehmd9OuLZdUHltkCP/TKcq1vNeDwE_xRNwTvMTtRN/zKU/0SMyT/Eb1XNawk";
s.async = true;
s.referrerPolicy = 'no-referrer-when-downgrade';
l.parentNode.insertBefore(s, l);
})({})
</script>
"""

# <head> snippet(s): popunder bootstrap + any site-wide scripts.
AD_HEAD = POPUNDER

# In-article slots. Keep these self-contained; empty string = no slot rendered.
AD_SLOT_1 = INPAGE_PUSH
AD_SLOT_2 = BANNER_300x250

# ads.txt lines (one authorized seller per line).
# HilltopAds does NOT issue or require an authorized-seller line for MultiTag/Popunder
# zones: tags are served from their own script hosts (subtle-injury.com /
# unfoldedtrade.com) and the publisher panel has no ads.txt entry.
# So ads.txt stays empty (sitegen only writes the file when this is non-empty).
ADS_TXT = ""
