"""Ranking findings so a plumber with ten minutes looks at the right three.

A sweep returns 147 variants. Most are free and harmless -- nobody has bought
goodwinplurnbing.shop and nobody will. The dangerous ones share properties, and they are not
the ones a naive list would put first.

The ordering that matters:
  1. Someone already registered it AND it is ranking in search for the brand -> live scam.
  2. Someone already registered it -> a loaded gun, whether or not it is firing yet.
  3. Free, but it fools the eye -> cheap to take away from an attacker forever.
  4. Free and awkward to reach -> ignore it. Registering everything is how brand-protection
     invoices reach five figures for no benefit.
"""
from __future__ import annotations

TECHNIQUE_WEIGHT = {
    "reads the same": 30,        # rn/m, l/1 -- indistinguishable in a browser bar
    "other tld": 24,             # customers genuinely believe .com belongs to you
    "transposed": 18,
    "fat finger": 15,
    "dropped character": 12,
    "doubled character": 8,
    "looks official": 20,        # "secure-yourbrand.com" reads like your payment page
}


def score(*, technique: str, registered: bool | None, ranking: bool = False,
          resolves: bool = False, destination: str | None = None) -> int:
    """0-100. Registered-and-ranking dominates everything else, because that is the case where
    a customer is being taken today rather than hypothetically."""
    # Owned by the business itself. Measured against a real estate: five of six registered
    # Pimlico Plumbers lookalikes redirect to the real site. Scoring those as impersonation
    # would be wrong five times out of six, and a business cried wolf at stops reading.
    if destination == "ours":
        return 0

    base = TECHNIQUE_WEIGHT.get(technique, 10)
    if registered is None:
        return min(base, 40)                    # unknown availability: do not over-claim
    if not registered:
        # Free: a risk you can close rather than one in progress -- but a free domain that
        # fools the eye is the cheapest win available, so it must clear "worth taking".
        # Without the lift, every unregistered homoglyph scored 30 and landed in "ignore",
        # which contradicted this module's own docstring.
        return min(base + 10, 45)
    s = 50 + base                               # someone owns a lookalike of your name
    if resolves:
        s += 10                                 # and it serves a page
    if ranking:
        s += 25                                 # and your customers are being shown it
    return min(s, 100)


def band(s: int) -> str:
    if s == 0: return "already yours"
    if s >= 85: return "live scam"
    if s >= 60: return "held by someone else"
    if s >= 35: return "worth taking"
    return "ignore"


def advice(*, registered: bool | None, ranking: bool, technique: str) -> str:
    if registered and ranking:
        return ("Someone owns this and your customers are being shown it in search. "
                "Evidence first, then registrar abuse report — do not tip them off.")
    if registered:
        return "Someone else owns this. Watch it. If it starts serving a page, escalate."
    if registered is False:
        return "Free. Registering it costs about a tenth of one job and closes it permanently."
    return "Availability unknown — no advice until we have checked."


def brand_similarity(host: str, real_domain: str) -> float:
    """How much a ranking host looks like the brand's own domain, 0..1.

    Needed because "ranking for your name" is not the same as "pretending to be you".
    Checkatrade, Yell and Facebook all rank for a plumber's name and none of them are
    impersonating him. Scoring every non-owned result as a live scam would send a business
    to file abuse reports against its own review sites -- a false positive with real cost.
    """
    from difflib import SequenceMatcher
    stem = real_domain.split(".")[0].lower()
    h = host.split(".")[0].lower()
    if stem in h or h in stem:
        return 1.0
    return SequenceMatcher(None, stem, h).ratio()


#: Below this, a host ranking for the brand is treated as a mention, not an impersonation.
IMPERSONATION_THRESHOLD = 0.72


#: A search hit can never be auto-labelled a live scam, however similar the name.
#: pimlicoplumbersfranchise.co.uk contains "pimlicoplumbers" and scored 100 -- it is Pimlico's
#: own franchise site. Sub-brands (franchise, careers, shop) and attackers are
#: string-identical; only a human can tell them apart, so the tool must not claim to.
SEARCH_HIT_CEILING = 74


def rank_finding_score(host: str, real_domain: str) -> tuple[int, str]:
    """Score something that ranks for the brand but was not a generated variant.

    Capped below the 'live scam' band on purpose. Calling a company's own franchise site a
    scam is not a nuisance false positive -- it is the product recommending an abuse report
    against its own user.
    """
    sim = brand_similarity(host, real_domain)
    if sim >= IMPERSONATION_THRESHOLD:
        return SEARCH_HIT_CEILING, "uses your name — check this is yours"
    # A directory, review site or marketplace. Worth a human glance, never an abuse report.
    return 22, "mentions you"
