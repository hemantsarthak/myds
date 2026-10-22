"""engine/analytics.py — the ONE place the pageview-counter snippet lives.

Our Cloudflare API token has no Web Analytics (RUM) permission, so traffic is counted
by the self-hosted Worker in `workers/analytics/` (see docs/ANALYTICS.md). Cookie-free,
no external services, no CORS.

Usage (Lead wires this in; do not edit engine/sitegen.py from here):

    from engine.analytics import analytics_tag
    extra_head = analytics_tag("ifsc")

The base URL comes from the `ANALYTICS_URL` env var (shared/.env, or any process env) and
falls back to the deployed worker URL.
"""

import os

DEFAULT_ANALYTICS_URL = "https://analytics.monetec2.workers.dev"


def analytics_url() -> str:
    """Base URL of the analytics Worker, e.g. https://analytics.monetec2.workers.dev."""
    return os.environ.get("ANALYTICS_URL", DEFAULT_ANALYTICS_URL).rstrip("/")


def analytics_tag(site_slug: str) -> str:
    """Return the <script> tag that counts pageviews for one site.

    `site_slug` must match the slug passed to `python scripts/ops.py stats --site ...`
    (lowercase letters/digits/hyphens, e.g. "ifsc", "pincode-india").
    Returns "" for an empty slug so callers can safely skip injection.
    """
    slug = (site_slug or "").strip()
    if not slug:
        return ""
    return f'<script defer src="{analytics_url()}/e.js?site={slug}"></script>'
