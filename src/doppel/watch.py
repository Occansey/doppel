"""What changed since last time.

A single sweep tells a business what is true today. The thing that actually protects them is
the second sweep: a lookalike that was free last week and is registered this morning is
somebody preparing to use it, and that is the only moment when acting is both cheap and early.

Nobody reads a weekly report of 61 unchanged rows. So this emits changes only, and ranks them
by whether the situation got worse.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Ordered worst-first. The wording is what a business owner reads in an alert, so it says
#: what happened and what it means, not which field changed.
ESCALATIONS = {
    "now_ranking": ("Your customers are now being shown it",
                    "It was registered before, but it has started appearing in search results "
                    "for your name. This is the point where people start paying the wrong person."),
    "newly_registered": ("Somebody just bought it",
                         "This was free at the last check. Someone has taken it. Nobody registers "
                         "a misspelling of your business by accident."),
    "now_resolving": ("It has started serving a page",
                      "It was parked. There is now a site there."),
}
DE_ESCALATIONS = {
    "dropped": ("It has been released",
                "Whoever held it let it lapse. It is free right now — taking it closes this "
                "permanently, and it will not stay free."),
    "no_longer_ranking": ("It has fallen out of search results",
                          "Still registered, but no longer being shown for your name."),
}
RANK = ["now_ranking", "newly_registered", "now_resolving", "dropped", "no_longer_ranking"]


@dataclass(frozen=True)
class Change:
    domain: str
    kind: str
    headline: str
    detail: str
    worse: bool


def _state(f: dict) -> tuple[bool | None, bool]:
    return f.get("registered"), "ranking" in (f.get("source") or "")


def diff(previous: list[dict], current: list[dict]) -> list[Change]:
    """Compare two sweeps of the same case. Unknown availability never produces a change --
    a fixture run followed by a live run must not look like an attack."""
    before = {f["label"]: f for f in previous}
    out: list[Change] = []

    for f in current:
        prev = before.get(f["label"])
        if not prev:
            continue                                   # new to the list, not a change in state
        was_reg, was_rank = _state(prev)
        now_reg, now_rank = _state(f)
        if was_reg is None or now_reg is None:
            continue                                   # never infer movement from a gap

        kind = None
        if not was_reg and now_reg:
            kind = "newly_registered"
        elif was_reg and not now_reg:
            kind = "dropped"
        elif was_reg and now_reg and not was_rank and now_rank:
            kind = "now_ranking"
        elif was_reg and now_reg and was_rank and not now_rank:
            kind = "no_longer_ranking"
        if not kind:
            continue

        worse = kind in ESCALATIONS
        head, det = (ESCALATIONS if worse else DE_ESCALATIONS)[kind]
        out.append(Change(domain=f["label"], kind=kind, headline=head, detail=det, worse=worse))

    out.sort(key=lambda c: RANK.index(c.kind))
    return out


def summary(changes: list[Change]) -> str:
    if not changes:
        return "Nothing changed since the last sweep."
    worse = [c for c in changes if c.worse]
    if not worse:
        return f"{len(changes)} change(s), none of them worse."
    return f"{len(worse)} thing(s) got worse since the last sweep."
