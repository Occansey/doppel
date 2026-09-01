"""The ICANN deletion clock.

A domain does not disappear on its expiry date. It walks a defined sequence of phases, and the
family almost always discovers the problem at the moment the site goes dark -- which is the
start of Redemption, not expiry. By then roughly half the recoverable window is already spent.

Durations below are the gTLD defaults. Registrars vary the auto-renew grace period (0-45 days),
so a real registrar value overrides the default wherever we have one; `Clock.source` records
which was used, because a date presented without its provenance is a guess wearing a suit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

AUTO_RENEW_GRACE_DAYS = 30      # registrar-dependent; ICANN permits 0-45
REDEMPTION_DAYS = 30            # ICANN Redemption Grace Period, fixed
PENDING_DELETE_DAYS = 5         # fixed; nothing can be restored during this window


class Phase(str, Enum):
    ACTIVE = "active"
    AUTO_RENEW_GRACE = "auto_renew_grace"
    REDEMPTION = "redemption"
    PENDING_DELETE = "pending_delete"
    RELEASED = "released"


#: What the family can still do, per phase. This is the whole product in one table.
RECOVERABLE = {
    Phase.ACTIVE: True,
    Phase.AUTO_RENEW_GRACE: True,       # cheap: an ordinary renewal
    Phase.REDEMPTION: True,             # expensive: a restore fee, often 8-15x a renewal
    Phase.PENDING_DELETE: False,        # impossible, at any price
    Phase.RELEASED: False,              # gone; may already belong to someone else
}

#: Whether the site is still reachable. The cruelty is that this flips to False at the exact
#: moment recovery stops being cheap -- so the visible signal arrives after the affordable window.
RESOLVES = {
    Phase.ACTIVE: True,
    Phase.AUTO_RENEW_GRACE: True,
    Phase.REDEMPTION: False,
    Phase.PENDING_DELETE: False,
    Phase.RELEASED: False,
}


@dataclass(frozen=True)
class Clock:
    domain: str
    expires_on: date
    phase: Phase
    recoverable: bool
    resolves: bool
    unrecoverable_on: date          # the date after which no money can bring it back
    days_left: int                  # days until that date; 0 once passed
    source: str                     # where expires_on came from

    @property
    def lost(self) -> bool:
        return not self.recoverable


def assess(domain: str, expires_on: date, *, today: date,
           auto_renew_grace_days: int = AUTO_RENEW_GRACE_DAYS,
           source: str = "name.com registration record") -> Clock:
    """Place a domain on the lifecycle. `today` is required, never defaulted to the wall clock:
    a deadline that silently depends on when the function ran is not testable."""
    if auto_renew_grace_days < 0:
        raise ValueError("auto_renew_grace_days cannot be negative")

    grace_ends = expires_on + timedelta(days=auto_renew_grace_days)
    redemption_ends = grace_ends + timedelta(days=REDEMPTION_DAYS)
    pending_ends = redemption_ends + timedelta(days=PENDING_DELETE_DAYS)

    if today <= expires_on:
        phase = Phase.ACTIVE
    elif today <= grace_ends:
        phase = Phase.AUTO_RENEW_GRACE
    elif today <= redemption_ends:
        phase = Phase.REDEMPTION
    elif today <= pending_ends:
        phase = Phase.PENDING_DELETE
    else:
        phase = Phase.RELEASED

    # The deadline that matters is the end of Redemption: the last day money still works.
    return Clock(
        domain=domain,
        expires_on=expires_on,
        phase=phase,
        recoverable=RECOVERABLE[phase],
        resolves=RESOLVES[phase],
        unrecoverable_on=redemption_ends,
        days_left=max(0, (redemption_ends - today).days),
        source=source,
    )
