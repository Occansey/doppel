"""Outward calls: SerpApi for who is ranking, name.com for who owns what.

Both fall back to fixtures without keys, and every result carries whether it was live. A
console that cannot tell you which is which would let someone file an abuse report against a
domain that was never checked.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

SERPAPI = "https://serpapi.com/search.json"
SANDBOX, LIVE = "https://api.dev.name.com", "https://api.name.com"


@dataclass
class Sourced:
    value: object
    live: bool
    source: str


def namecom_base() -> str:
    # Sandbox unless deliberately overridden. Registration spends real money.
    return LIVE if os.getenv("NAMECOM_LIVE") == "1" else SANDBOX


def _auth() -> tuple[str, str] | None:
    u, t = os.getenv("NAMECOM_USER"), os.getenv("NAMECOM_TOKEN")
    return (u, t) if u and t else None


# ------------------------------------------------------------------ name.com: who owns what
def availability(domains: list[str]) -> Sourced:
    """Bulk availability. One call per batch -- 147 individual lookups would be slow and rude."""
    auth = _auth()
    if not auth:
        taken = _FIXTURE_TAKEN
        return Sourced({d: {"registered": d in taken,
                            "price": None if d in taken else 12.99} for d in domains},
                       live=False, source="fixture · no name.com credentials")
    out: dict[str, dict] = {}
    with httpx.Client(timeout=30, auth=auth) as c:
        for i in range(0, len(domains), 50):                 # name.com caps the batch
            batch = domains[i:i + 50]
            r = c.get(f"{namecom_base()}/v4/domains:checkAvailability",
                      params=[("domainNames", d) for d in batch])
            if r.status_code != 200:
                continue
            for row in r.json().get("results", []):
                out[row["domainName"]] = {
                    "registered": not row.get("purchasable", False),
                    "price": row.get("purchasePrice"),
                }
    for d in domains:
        out.setdefault(d, {"registered": None, "price": None})
    return Sourced(out, live=True, source=f"name.com availability ({namecom_base()})")


def register(domain: str, years: int = 1) -> Sourced:
    """Claim a dangerous lookalike. Only ever called behind an explicit confirmation."""
    auth = _auth()
    if not auth:
        return Sourced({"ok": False}, live=False,
                       source="fixture · would POST /v4/domains (no credentials)")
    with httpx.Client(timeout=40, auth=auth) as c:
        r = c.post(f"{namecom_base()}/v4/domains",
                   json={"domain": {"domainName": domain}, "years": years})
        return Sourced({"ok": r.status_code < 300, "status": r.status_code,
                        "body": r.text[:400]}, live=True,
                       source=f"name.com register ({namecom_base()})")


def redirect(domain: str, to_host: str) -> Sourced:
    """Point a held lookalike at the real site, so a mistyped address still lands correctly.
    This is the payoff: the attacker's best domains now work *for* the business."""
    auth = _auth()
    if not auth:
        return Sourced({"ok": False}, live=False,
                       source=f"fixture · would CNAME {domain} -> {to_host}")
    with httpx.Client(timeout=30, auth=auth) as c:
        r = c.post(f"{namecom_base()}/v4/domains/{domain}/records",
                   json={"host": "", "type": "CNAME", "answer": to_host, "ttl": 300})
        return Sourced({"ok": r.status_code < 300, "status": r.status_code,
                        "body": r.text[:400]}, live=True,
                       source=f"name.com DNS ({namecom_base()})")


# ------------------------------------------------------------------ SerpApi: who is ranking
def who_ranks(business: str, anchors: list[str], real_domain: str) -> Sourced:
    """Anything ranking for the business name that is not the business. This is what turns a
    hypothetical lookalike into a scam in progress."""
    key = os.getenv("SERPAPI_KEY")
    q = " ".join([f'"{business}"', *anchors])
    if not key:
        return Sourced(_FIXTURE_RANKING, live=False, source=f"fixture · would query: {q}")
    hits = []
    with httpx.Client(timeout=25) as c:
        for engine in ("google", "google_local"):
            r = c.get(SERPAPI, params={"engine": engine, "q": q, "api_key": key})
            if r.status_code != 200:
                continue
            d = r.json()
            for block in ("organic_results", "local_results"):
                for item in (d.get(block) or [])[:10]:
                    link = item.get("link") or item.get("website") or ""
                    host = link.split("//")[-1].split("/")[0].removeprefix("www.").lower()
                    if not host or host == real_domain:
                        continue                    # the business itself is not a finding
                    hits.append({"host": host, "url": link,
                                 "label": item.get("title") or item.get("name") or host,
                                 "snippet": (item.get("snippet") or "")[:220],
                                 "engine": engine, "position": item.get("position")})
    return Sourced(hits, live=True, source=f"serpapi · {q}")


# ------------------------------------------------------------------ fixtures
#: Two lookalikes already taken -- one of them ranking. Without a taken-and-ranking case the
#: demo shows only hypotheticals, which is the thing this product exists to move past.
_FIXTURE_TAKEN = {
    "goodwinplurnbing.co.uk",      # rn/m homoglyph -- the live scam
    "goodwinplumbing.com",         # .com held by a squatter, parked
}

_FIXTURE_RANKING = [
    {"host": "goodwinplurnbing.co.uk", "url": "https://goodwinplurnbing.co.uk",
     "label": "Goodwin Plumbing — Emergency Callout, Book Online",
     "snippet": "24/7 emergency plumbing in Wallsend. Pay deposit online to secure your slot.",
     "engine": "google", "position": 3},
    {"host": "checkatrade.example.test", "url": "https://checkatrade.example.test/goodwin",
     "label": "Goodwin Plumbing reviews", "snippet": "412 verified reviews.",
     "engine": "google", "position": 5},
]
