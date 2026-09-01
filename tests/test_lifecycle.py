from datetime import date, timedelta
import pytest
from pending_delete.lifecycle import assess, Phase, REDEMPTION_DAYS, PENDING_DELETE_DAYS

EXP = date(2026, 9, 1)


def at(day_offset: int, **kw):
    return assess("example.com", EXP, today=EXP + timedelta(days=day_offset), **kw)


def test_phase_boundaries_are_inclusive_and_contiguous():
    assert at(0).phase is Phase.ACTIVE            # expiry day itself is still active
    assert at(1).phase is Phase.AUTO_RENEW_GRACE
    assert at(30).phase is Phase.AUTO_RENEW_GRACE  # last grace day
    assert at(31).phase is Phase.REDEMPTION
    assert at(60).phase is Phase.REDEMPTION        # last redeemable day
    assert at(61).phase is Phase.PENDING_DELETE
    assert at(65).phase is Phase.PENDING_DELETE
    assert at(66).phase is Phase.RELEASED


def test_the_cruelty_the_product_exists_for():
    """The site goes dark exactly when recovery stops being cheap, so the only visible
    signal arrives after the affordable window has closed."""
    last_cheap_day = at(30)
    assert last_cheap_day.resolves and last_cheap_day.recoverable

    first_dark_day = at(31)
    assert not first_dark_day.resolves      # the family finally notices here...
    assert first_dark_day.recoverable       # ...and it is still saveable, but no longer cheaply


def test_days_left_counts_to_the_last_day_money_works():
    assert at(0).days_left == 60
    assert at(60).days_left == 0            # final redeemable day
    assert at(61).days_left == 0            # pending delete: no amount of money helps
    assert at(999).days_left == 0


def test_nothing_is_recoverable_once_pending_delete_starts():
    for d in (61, 65, 66, 400):
        assert at(d).lost, f"day {d} should be unrecoverable"


def test_registrar_specific_grace_shifts_every_downstream_date():
    """Registrars set the auto-renew grace between 0 and 45 days. A build that hardcodes 30
    would tell a family the wrong deadline -- the exact failure this product must not have."""
    zero = at(1, auto_renew_grace_days=0)
    assert zero.phase is Phase.REDEMPTION          # no grace at all: straight to dark
    assert zero.unrecoverable_on == EXP + timedelta(days=REDEMPTION_DAYS)

    long = at(40, auto_renew_grace_days=45)
    assert long.phase is Phase.AUTO_RENEW_GRACE    # still cheap where the default says dark


def test_total_window_matches_icann_arithmetic():
    c = at(0)
    released = c.unrecoverable_on + timedelta(days=PENDING_DELETE_DAYS)
    assert (released - EXP).days == 30 + REDEMPTION_DAYS + PENDING_DELETE_DAYS == 65


def test_a_date_must_carry_its_provenance():
    assert at(0).source == "name.com registration record"
    assert assess("x.com", EXP, today=EXP, source="whois fallback").source == "whois fallback"


def test_negative_grace_is_rejected_rather_than_silently_clamped():
    with pytest.raises(ValueError):
        at(0, auto_renew_grace_days=-1)
