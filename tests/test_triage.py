from doppel.triage import score, band, advice


def test_a_live_scam_outranks_everything():
    live = score(technique="reads the same", registered=True, ranking=True, resolves=True)
    held = score(technique="reads the same", registered=True)
    free = score(technique="reads the same", registered=False)
    assert live > held > free
    assert band(live) == "live scam"


def test_free_never_reaches_the_urgent_bands():
    """A free domain is a risk you can close today, not one in progress. Ranking it as
    urgent is how brand-protection tools bury the real incident."""
    for t in ("reads the same", "other tld", "looks official"):
        assert band(score(technique=t, registered=False)) in ("worth taking", "ignore")


def test_unknown_availability_does_not_over_claim():
    assert score(technique="reads the same", registered=None) <= 40
    assert "unknown" in advice(registered=None, ranking=False, technique="reads the same")


def test_eye_fooling_beats_awkward_typos_at_equal_status():
    assert (score(technique="reads the same", registered=False)
            > score(technique="doubled character", registered=False))


def test_advice_for_a_live_scam_says_evidence_before_confrontation():
    a = advice(registered=True, ranking=True, technique="reads the same")
    assert "Evidence first" in a and "do not tip them off" in a


def test_scores_stay_in_range():
    for r in (None, True, False):
        for t in ("reads the same", "unknown-technique"):
            s = score(technique=t, registered=r, ranking=True, resolves=True)
            assert 0 <= s <= 100


def test_a_free_eye_fooling_variant_is_worth_taking_not_ignorable():
    """The cheapest win in the whole product is registering a free homoglyph. An earlier
    scoring pass buried these in 'ignore', contradicting the module docstring."""
    s = score(technique="reads the same", registered=False)
    assert band(s) == "worth taking", f"scored {s}"


def test_junk_typos_stay_ignorable_even_when_free():
    assert band(score(technique="doubled character", registered=False)) == "ignore"


def test_a_review_site_ranking_for_you_is_not_an_impersonator():
    """Checkatrade ranks for every plumber's name. Calling that a live scam would send a
    business to file abuse reports against its own review site."""
    from doppel.triage import rank_finding_score
    risk, kind = rank_finding_score("checkatrade.example.test", "goodwinplumbing.co.uk")
    assert kind == "mentions you"
    assert band(risk) == "ignore"


def test_a_search_discovered_lookalike_is_flagged_but_not_accused():
    """This test previously asserted 'live scam'. That was wrong: the same code path also
    matched pimlicoplumbersfranchise.co.uk, which is the brand's own franchise site. A host
    found only in search results is flagged for a human, never auto-accused. A generated
    lookalike that is registered and ranking still reaches 'live scam' via score()."""
    from doppel.triage import rank_finding_score
    risk, kind = rank_finding_score("goodwinplurnbing.co.uk", "goodwinplumbing.co.uk")
    assert band(risk) == "held by someone else"
    assert "check this is yours" in kind


def test_similarity_recognises_containment_and_near_misses():
    from doppel.triage import brand_similarity
    assert brand_similarity("goodwinplumbing-uk.com", "goodwinplumbing.co.uk") == 1.0
    assert brand_similarity("facebook.com", "goodwinplumbing.co.uk") < 0.5


def test_availability_is_posted_not_queried():
    """name.com answers 405 to a GET on domains:checkAvailability. This shape mistake would
    only have surfaced once credentials started working -- i.e. on the day of the demo."""
    import inspect
    from doppel import adapters
    src = inspect.getsource(adapters.availability)
    assert ".post(" in src and "checkAvailability" in src
    assert 'params=[("domainNames"' not in src


def test_a_lookalike_that_redirects_to_you_scores_zero():
    """Measured on a real estate: five of six registered Pimlico lookalikes point at the
    real site. Alarming on those is the fastest way to make the tool ignorable."""
    s = score(technique="reads the same", registered=True, ranking=True,
              resolves=True, destination="ours")
    assert s == 0 and band(s) == "already yours"


def test_destination_only_excuses_a_domain_when_it_is_actually_ours():
    for dest in ("parked", "elsewhere", "unreachable", None):
        assert score(technique="reads the same", registered=True, destination=dest) > 0


def test_a_search_hit_can_never_be_auto_labelled_a_live_scam():
    """pimlicoplumbersfranchise.co.uk contains the brand exactly and ranks for it -- and is
    Pimlico's own franchise site. It scored 100. A sub-brand and an attacker are
    string-identical; only a human can tell them apart."""
    from doppel.triage import rank_finding_score
    risk, kind = rank_finding_score("pimlicoplumbersfranchise.co.uk", "pimlicoplumbers.com")
    assert band(risk) != "live scam"
    assert "check this is yours" in kind


def test_only_a_generated_lookalike_that_is_registered_and_ranking_reaches_live_scam():
    top = score(technique="reads the same", registered=True, ranking=True, resolves=True)
    assert band(top) == "live scam"
