"""engine/ads.py — the ONE place ad network snippets live.

When an ad network account exists, paste the snippets here, set MONETIZATION_ON = True,
rebuild every site (`python scripts/build_all.py`) and redeploy. Do not scatter tags.

Networks planned: Monetag (instant approval, crypto payout), Adsterra (backup),
Ezoic / AdSense later (human KYC).
"""

MONETIZATION_ON = False

# <head> snippet(s): verification tags, popunder/push scripts, ad system bootstrap.
AD_HEAD = """
"""

# In-article slots. Keep these self-contained; empty string = no slot rendered.
AD_SLOT_1 = """
"""

AD_SLOT_2 = """
"""

# ads.txt lines (one authorized seller per line), e.g.
# "monetag.com, 1234567890, DIRECT"
ADS_TXT = ""
