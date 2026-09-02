import httpx
from doppel.destination import classify

REAL = "pimlicoplumbers.com"


def _client(final_url: str | None, boom: bool = False):
    def handler(request):
        if boom:
            raise httpx.ConnectError("no answer")
        return httpx.Response(200, request=request)
    transport = httpx.MockTransport(handler)
    c = httpx.Client(transport=transport, follow_redirects=True)
    if final_url:                       # pretend the redirect chain ended here
        c.get = lambda url: httpx.Response(200, request=httpx.Request("GET", final_url))
    return c


def test_a_lookalike_redirecting_to_the_real_site_is_ours_not_an_attack():
    """Five of six registered Pimlico lookalikes redirect to the real domain. Calling those
    impersonations would be wrong five times out of six."""
    d = classify("pimlicoplumbers.org", REAL, client=_client("https://www.pimlicoplumbers.com/"))
    assert d.verdict == "ours" and "No action needed" in d.detail


def test_a_domain_that_stays_on_itself_is_parked_and_needs_a_human():
    d = classify("pimlocoplumbers.com", REAL, client=_client("http://pimlocoplumbers.com/"))
    assert d.verdict == "parked" and "Worth looking at" in d.detail


def test_a_domain_sending_traffic_somewhere_else_is_flagged_with_where():
    d = classify("pimlocoplumbers.com", REAL, client=_client("https://casino-example.test/x"))
    assert d.verdict == "elsewhere" and "casino-example.test" in d.detail


def test_no_answer_is_held_not_used_rather_than_an_error():
    d = classify("nothing.example", REAL, client=_client(None, boom=True))
    assert d.verdict == "unreachable" and not d.reachable


def test_www_is_not_treated_as_a_different_site():
    d = classify("pimlicoplumbers.co.uk", REAL, client=_client("https://www.pimlicoplumbers.com/"))
    assert d.verdict == "ours"
