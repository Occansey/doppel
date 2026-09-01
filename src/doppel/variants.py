"""Generate the lookalike domains an attacker would actually register.

Not every permutation -- the useful set is small and specific. Registrars sell 300 TLDs and a
brand has thousands of possible misspellings, but the ones that take money from real customers
share three properties: they are typo-reachable from a phone keyboard, they read correctly at a
glance, or they sit on a TLD a customer would believe.

Every variant carries the technique that produced it, because a case file that says "we
registered 40 domains" is worth less than one that says why each was a risk.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Adjacent keys on a QWERTY phone keyboard. Typosquatting is a thumb problem, not a spelling one.
NEIGHBOURS = {
    "a": "qwsz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wsdr", "f": "drtgvc",
    "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn", "k": "jiolm", "l": "kop",
    "m": "njk", "n": "bhjm", "o": "iklp", "p": "ol", "q": "wa", "r": "edft", "s": "awedxz",
    "t": "rfgy", "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu", "z": "asx",
}

#: Characters that survive a glance. rn/m is the classic; the rest are equally cheap.
GLYPHS = {"m": ["rn"], "rn": ["m"], "l": ["1", "i"], "i": ["l", "1"], "o": ["0"],
          "0": ["o"], "w": ["vv"], "cl": ["d"], "d": ["cl"], "5": ["s"], "s": ["5"]}

#: TLDs a customer plausibly believes belong to the same business.
BELIEVABLE_TLDS = ["com", "net", "co", "co.uk", "org", "shop", "online", "site", "store"]

#: Words that make a fake look like an official sub-brand.
PREFIXES = ["my", "the", "get", "book", "pay", "secure", "official"]
SUFFIXES = ["online", "official", "payments", "booking", "support", "ltd", "uk"]


@dataclass(frozen=True)
class Variant:
    domain: str
    technique: str
    why: str            # plain English, for the case file and for the customer-facing report


def _split(domain: str) -> tuple[str, str]:
    parts = domain.lower().strip().split(".", 1)
    if len(parts) != 2:
        raise ValueError(f"expected name.tld, got {domain!r}")
    return parts[0], parts[1]


def typos(stem: str) -> set[tuple[str, str]]:
    out = set()
    for i, ch in enumerate(stem):
        for n in NEIGHBOURS.get(ch, ""):
            out.add((stem[:i] + n + stem[i + 1:], "fat finger"))     # substitution
        out.add((stem[:i] + stem[i + 1:], "dropped character"))       # omission
        if i:
            out.add((stem[:i - 1] + ch + stem[i - 1] + stem[i + 1:], "transposed"))
        out.add((stem[:i] + ch + ch + stem[i:], "doubled character"))
    return {(s, t) for s, t in out if s and s != stem}


def glyphs(stem: str) -> set[tuple[str, str]]:
    out = set()
    for src, repls in GLYPHS.items():
        idx = stem.find(src)
        if idx < 0:
            continue
        for r in repls:
            out.add((stem[:idx] + r + stem[idx + len(src):], "reads the same"))
    return {(s, t) for s, t in out if s != stem}


def affixes(stem: str) -> set[tuple[str, str]]:
    out = {(p + stem, "looks official") for p in PREFIXES}
    out |= {(stem + s, "looks official") for s in SUFFIXES}
    out |= {(f"{p}-{stem}", "looks official") for p in PREFIXES}
    out |= {(f"{stem}-{s}", "looks official") for s in SUFFIXES}
    return out


WHY = {
    "fat finger": "One key away on a phone keyboard. Customers reach it by accident.",
    "dropped character": "A missed keystroke lands here.",
    "transposed": "Two letters swapped — the most common typing error there is.",
    "doubled character": "A held key lands here.",
    "reads the same": "Visually identical at a glance in a browser bar or an email.",
    "looks official": "Reads like your own booking or payment page.",
    "other tld": "Same name, a suffix your customers would believe.",
}


def generate(domain: str, *, limit: int = 120) -> list[Variant]:
    """Ranked, de-duplicated, and capped. The cap is deliberate: a list nobody reads protects
    nobody, and every entry costs a live availability call."""
    stem, tld = _split(domain)
    seen: dict[str, Variant] = {}

    def add(name: str, t: str, target_tld: str) -> None:
        d = f"{name}.{target_tld}"
        if d == domain or d in seen:
            return
        seen[d] = Variant(d, t, WHY[t])

    for name, t in glyphs(stem):          # highest risk first: these fool the eye
        add(name, t, tld)
    for name, t in typos(stem):
        add(name, t, tld)
    for other in BELIEVABLE_TLDS:          # same name, believable suffix
        if other != tld:
            add(stem, "other tld", other)
    for name, t in affixes(stem):
        add(name, t, tld)

    order = {"reads the same": 0, "other tld": 1, "transposed": 2, "fat finger": 3,
             "dropped character": 4, "doubled character": 5, "looks official": 6}
    ranked = sorted(seen.values(), key=lambda v: (order[v.technique], len(v.domain)))
    return ranked[:limit]
