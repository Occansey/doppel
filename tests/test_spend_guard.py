import os
import pytest
from doppel import adapters
from doppel.adapters import WouldSpendRealMoney


def _prod(monkeypatch, allow=None):
    monkeypatch.setenv("NAMECOM_LIVE", "1")
    monkeypatch.setenv("NAMECOM_USER", "u"); monkeypatch.setenv("NAMECOM_TOKEN", "t")
    monkeypatch.delenv("DOPPEL_ALLOW_SPEND", raising=False)
    if allow:
        monkeypatch.setenv("DOPPEL_ALLOW_SPEND", allow)


def test_registering_against_production_is_refused_by_default(monkeypatch):
    """The dev sandbox is unavailable on this account, so the credentials that run a free
    availability sweep would also complete a purchase. A demo click must not be one keystroke
    from buying a domain."""
    _prod(monkeypatch)
    with pytest.raises(WouldSpendRealMoney):
        adapters.register("example-doppel-test.com")


def test_dns_writes_against_production_are_refused_too(monkeypatch):
    _prod(monkeypatch)
    with pytest.raises(WouldSpendRealMoney):
        adapters.redirect("example-doppel-test.com", "goodwinplumbing.co.uk")


def test_the_guard_names_the_escape_hatch(monkeypatch):
    _prod(monkeypatch)
    with pytest.raises(WouldSpendRealMoney, match="DOPPEL_ALLOW_SPEND=1"):
        adapters.register("example-doppel-test.com")


def test_sandbox_writes_are_never_guarded(monkeypatch):
    monkeypatch.delenv("NAMECOM_LIVE", raising=False)
    monkeypatch.delenv("NAMECOM_USER", raising=False)
    monkeypatch.delenv("NAMECOM_TOKEN", raising=False)
    r = adapters.register("example-doppel-test.com")      # fixture path, no exception
    assert r.live is False


def test_availability_is_never_guarded_because_reads_are_free(monkeypatch):
    """The whole sweep must keep working against production -- it costs nothing."""
    _prod(monkeypatch)
    import inspect
    assert "_guard_spend" not in inspect.getsource(adapters.availability)


def test_a_bare_row_is_never_read_as_registered_without_a_retry():
    """name.com omits `purchasable` for domains it did not resolve in a large batch, not only
    for taken ones. Reading absence as 'registered' reported 33 free lookalikes as owned by
    attackers -- a false accusation, and it would have been the centrepiece of the demo."""
    import inspect
    src = inspect.getsource(adapters.availability)
    assert "unresolved" in src, "ambiguous rows must be re-queried"
    assert "range(0, len(unresolved), 5)" in src, "retry must use a small batch"
    assert 'not row.get("purchasable", False)' not in src, "the buggy default must not return"
