"""Outward calls: SerpApi for discovery, name.com for the registration record.

Both fall back to fixtures when no key is present, and every result says which mode produced
it. A console that cannot tell you whether a deadline came from a live registry or a fixture
is worse than useless here -- it would let someone plan a funeral week around a made-up date.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

SERPAPI = "https://serpapi.com/search.json"
NAMECOM_SANDBOX = "https://api.dev.name.com"
NAMECOM_LIVE = "https://api.name.com"


@dataclass
class Sourced:
    """A value plus where it came from. Nothing in this product travels without provenance."""
    value: object
    live: bool
    source: str


def _namecom_base() -> str:
    # Sandbox unless someone deliberately says otherwise. Registering a domain spends money.
    return NAMECOM_LIVE if os.getenv("NAMECOM_LIVE") == "1" else NAMECOM_SANDBOX


# --------------------------------------------------------------------------- discovery
def discover(name: str, anchors: list[str]) -> Sourced:
    """Find the person's public footprint. The family typically knows one or two of these."""
    key = os.getenv("SERPAPI_KEY")
    query = " ".join([f'"{name}"', *anchors])
    if not key:
        return Sourced(_FIXTURE_RESULTS, live=False, source=f"fixture · would query: {query}")

    out = []
    with httpx.Client(timeout=25) as c:
        for engine, extra in (("google", {}), ("google_news", {}), ("google_local", {})):
            r = c.get(SERPAPI, params={"engine": engine, "q": query, "api_key": key, **extra})
            if r.status_code != 200:
                continue
            d = r.json()
            for block in ("organic_results", "news_results", "local_results"):
                for item in (d.get(block) or [])[:10]:
                    link = item.get("link") or item.get("website")
                    if not link:
                        continue
                    out.append({
                        "label": item.get("title") or item.get("name") or link,
                        "url": link,
                        "snippet": (item.get("snippet") or item.get("description") or "")[:240],
                        "engine": engine,
                    })
    return Sourced(out, live=True, source=f"serpapi · {query}")


# --------------------------------------------------------------------------- registration
def registration(domain: str) -> Sourced:
    """Read the real expiry and registrar. This is the number the whole product hangs on."""
    user, token = os.getenv("NAMECOM_USER"), os.getenv("NAMECOM_TOKEN")
    if not (user and token):
        row = _FIXTURE_DOMAINS.get(domain)
        if not row:
            return Sourced(None, live=False, source="fixture · unknown domain")
        return Sourced(row, live=False, source="fixture · not a live registry record")

    with httpx.Client(timeout=20, auth=(user, token)) as c:
        r = c.get(f"{_namecom_base()}/v4/domains/{domain}")
        if r.status_code == 404:
            # Not in this account. Availability still tells us whether it has been released.
            a = c.get(f"{_namecom_base()}/v4/domains:checkAvailability",
                      params={"domainNames": domain})
            avail = (a.json().get("results") or [{}])[0] if a.status_code == 200 else {}
            return Sourced({"expires_on": None, "registrar": None,
                            "purchasable": avail.get("purchasable"),
                            "purchase_price": avail.get("purchasePrice")},
                           live=True, source=f"name.com availability ({_namecom_base()})")
        r.raise_for_status()
        d = r.json()
        return Sourced({"expires_on": (d.get("expireDate") or "")[:10] or None,
                        "registrar": "name.com",
                        "autorenew": d.get("autorenewEnabled")},
                       live=True, source=f"name.com registration record ({_namecom_base()})")


# --------------------------------------------------------------------------- fixtures
#: A plausible estate. One domain still cheap to save, one already dark and costly, one past
#: rescue entirely -- because the demo has to show all three outcomes, including the loss.
_TODAY = date(2026, 9, 1)
_FIXTURE_DOMAINS = {
    "alanwhitfield.co.uk": {
        "expires_on": str(_TODAY + timedelta(days=9)),      # ACTIVE - renew now, cheaply
        "registrar": "name.com", "autorenew": False},
    "whitfieldarchive.org": {
        "expires_on": str(_TODAY - timedelta(days=41)),     # REDEMPTION - site already dark
        "registrar": "name.com", "autorenew": False},
    "whitfield-prints.com": {
        "expires_on": str(_TODAY - timedelta(days=64)),     # PENDING DELETE - unrecoverable
        "registrar": "name.com", "autorenew": False},
}

_FIXTURE_RESULTS = [
    {"label": "Alan Whitfield — Photography", "url": "https://alanwhitfield.co.uk",
     "snippet": "Forty years photographing the Tyne shipyards and the people who worked them.",
     "engine": "google"},
    {"label": "The Whitfield Archive", "url": "https://whitfieldarchive.org",
     "snippet": "11,400 catalogued negatives, 1968–2009. Used by three universities.",
     "engine": "google"},
    {"label": "Whitfield Prints", "url": "https://whitfield-prints.com",
     "snippet": "Darkroom prints to order. Established 1991.", "engine": "google"},
    {"label": "Obituary: Alan Whitfield, 1946–2026", "url": "https://example-news.test/obit/whitfield",
     "snippet": "The photographer who refused to let the yards be forgotten.",
     "engine": "google_news"},
    {"label": "Whitfield Studio", "url": "https://maps.example.test/whitfield-studio",
     "snippet": "Photography studio · Wallsend", "engine": "google_local"},
]
