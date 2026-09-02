from doppel.watch import diff, summary

def f(label, registered, ranking=False):
    return {"label": label, "registered": registered,
            "source": "name.com availability (live)" + (" · ranking: serpapi" if ranking else "")}


def test_a_free_domain_becoming_registered_is_the_headline_event():
    """Nobody registers a misspelling of your business by accident. This is the moment
    where acting is both cheap and early."""
    cs = diff([f("a.com", False)], [f("a.com", True)])
    assert [c.kind for c in cs] == ["newly_registered"]
    assert cs[0].worse


def test_starting_to_rank_outranks_being_bought():
    """Being shown to customers is worse than merely existing."""
    prev = [f("a.com", False), f("b.com", True)]
    cur = [f("a.com", True), f("b.com", True, ranking=True)]
    assert [c.kind for c in diff(prev, cur)] == ["now_ranking", "newly_registered"]


def test_a_dropped_domain_is_an_opportunity_not_an_alarm():
    c = diff([f("a.com", True)], [f("a.com", False)])[0]
    assert c.kind == "dropped" and not c.worse
    assert "free right now" in c.detail


def test_unchanged_rows_produce_nothing():
    same = [f("a.com", True), f("b.com", False)]
    assert diff(same, same) == []
    assert summary([]) == "Nothing changed since the last sweep."


def test_a_fixture_run_followed_by_a_live_run_is_not_an_attack():
    """Unknown availability must never look like movement -- otherwise the first real sweep
    after configuring credentials would fire alarms on every row."""
    unknown = {"label": "a.com", "registered": None, "source": "fixture"}
    assert diff([unknown], [f("a.com", True)]) == []
    assert diff([f("a.com", True)], [unknown]) == []


def test_domains_absent_from_the_previous_sweep_are_not_changes():
    assert diff([], [f("new.com", True)]) == []


def test_summary_counts_only_what_got_worse():
    cs = diff([f("a.com", True), f("b.com", False)], [f("a.com", False), f("b.com", True)])
    assert summary(cs) == "1 thing(s) got worse since the last sweep."
