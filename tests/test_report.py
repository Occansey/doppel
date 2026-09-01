from doppel.report import build

CASE = {"business_name": "Goodwin Plumbing", "domain": "goodwinplumbing.co.uk",
        "owner_email": "ray@goodwinplumbing.co.uk"}
HOSTILE = {"label": "goodwinplurnbing.co.uk", "technique": "reads the same",
           "registered": True, "status": "hostile",
           "source": "name.com availability (https://api.name.com)",
           "snippet": "Visually identical at a glance."}
LEDGER = [{"target": "goodwinplurnbing.co.uk", "at": "2026-09-01T09:12:00+00:00",
           "verb": "sweep", "result": "registered elsewhere"},
          {"target": "somethingelse.com", "at": "2026-09-01T09:12:00+00:00",
           "verb": "sweep", "result": "free"}]


def test_a_complete_case_produces_a_ready_report():
    r = build(case=CASE, finding=HOSTILE, ledger=LEDGER)
    assert r.ready and not r.missing
    assert "goodwinplurnbing.co.uk" in r.subject
    assert "Suspension of goodwinplurnbing.co.uk" in r.body


def test_only_evidence_about_this_domain_is_included():
    r = build(case=CASE, finding=HOSTILE, ledger=LEDGER)
    assert r.evidence_count == 1
    assert "somethingelse.com" not in r.body


def test_a_fixture_lookup_can_never_produce_a_ready_report():
    """A confident-looking abuse report built on fixture data would be worse than none."""
    f = {**HOSTILE, "source": "fixture · no name.com credentials"}
    r = build(case=CASE, finding=f, ledger=LEDGER)
    assert not r.ready
    assert any("fixture" in m for m in r.missing)


def test_an_unregistered_domain_has_nobody_to_report():
    r = build(case=CASE, finding={**HOSTILE, "registered": False}, ledger=LEDGER)
    assert not r.ready
    assert any("no party to report" in m for m in r.missing)


def test_an_untriaged_finding_is_not_reportable():
    r = build(case=CASE, finding={**HOSTILE, "status": "pending"}, ledger=LEDGER)
    assert not r.ready
    assert any("confirmed this is hostile" in m for m in r.missing)


def test_no_observations_says_so_rather_than_faking_a_date():
    r = build(case=CASE, finding=HOSTILE, ledger=[])
    assert "no observations recorded yet" in r.body
    assert "date not recorded" in r.body


def test_the_report_never_asserts_harm_it_cannot_evidence():
    """An earlier draft claimed customers had been defrauded -- a sentence nobody had
    evidenced, put in the business owner's mouth, inside a document that ends by promising
    the opposite."""
    r = build(case=CASE, finding=HOSTILE, ledger=LEDGER)
    for invented in ("believe they have paid us", "we have received contact"):
        assert invented not in r.body.lower()


def test_search_visibility_is_claimed_only_when_it_was_observed():
    quiet = {**HOSTILE, "risk": 60, "source": "name.com availability (live)"}
    assert "appears in search results" not in build(case=CASE, finding=quiet, ledger=LEDGER).body

    loud = {**HOSTILE, "risk": 100, "source": "name.com availability (live) · ranking: serpapi"}
    assert "appears in search results" in build(case=CASE, finding=loud, ledger=LEDGER).body
