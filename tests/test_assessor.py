from doppel.assessor import Assessment, assess, recommendation


class FakeModels:
    def __init__(self, payload): self.payload = payload
    def generate_content(self, model, contents):
        class R: text = self.payload
        return R()


class FakeClient:
    def __init__(self, payload): self.models = FakeModels(payload)


def test_a_verdict_without_evidence_is_discarded():
    """This feeds an abuse report a registrar will read. An unevidenced accusation is worse
    than no assessment."""
    a = assess("x.com", "y.com", _client=FakeClient(
        '{"verdict":"dressed_as_you","confidence":"high","reasoning":"looks bad","evidence":[]}'))
    assert a.verdict == "dressed_as_you" and not a.usable
    assert "decide this one yourself" in recommendation(a).lower()


def test_an_evidenced_impersonation_is_usable_and_still_only_a_recommendation():
    a = assess("x.com", "y.com", _client=FakeClient(
        '{"verdict":"dressed_as_you","confidence":"high","reasoning":"copied branding",'
        '"evidence":["Pimlico Plumbers","same phone number 0207 123"]}'))
    assert a.usable
    r = recommendation(a)
    assert "mark it 'hostile'" in r          # asks a human; never acts
    assert "we have" not in r.lower()


def test_the_franchise_case_the_rules_could_not_solve():
    """pimlicoplumbersfranchise.co.uk defeated string similarity. Looking at the page is
    the only thing that can tell a sub-brand from an impersonator."""
    a = assess("pimlicoplumbersfranchise.co.uk", "pimlicoplumbers.com", _client=FakeClient(
        '{"verdict":"same_organisation","confidence":"high","reasoning":"franchise arm",'
        '"evidence":["Pimlico Plumbers Franchise","part of the Pimlico Group"]}'))
    assert a.usable and a.verdict == "same_organisation"
    assert "your own site" in recommendation(a)


def test_an_unknown_verdict_string_is_coerced_not_trusted():
    a = assess("x.com", "y.com", _client=FakeClient(
        '{"verdict":"definitely_evil","confidence":"high","evidence":["x"]}'))
    assert a.verdict == "cannot_tell" and not a.usable


def test_unparseable_model_output_never_raises():
    a = assess("x.com", "y.com", _client=FakeClient("I think it's probably fine!"))
    assert a.verdict == "cannot_tell" and not a.usable


def test_fenced_json_is_accepted():
    a = assess("x.com", "y.com", _client=FakeClient(
        '```json\n{"verdict":"unrelated_business","confidence":"medium",'
        '"reasoning":"different trade","evidence":["Roofing since 1998"]}\n```'))
    assert a.usable and a.verdict == "unrelated_business"


def test_evidence_is_capped_so_a_verbose_model_cannot_flood_the_report():
    a = assess("x.com", "y.com", _client=FakeClient(
        '{"verdict":"dressed_as_you","confidence":"high","reasoning":"r",'
        '"evidence":["a","b","c","d","e","f"]}'))
    assert len(a.evidence) == 4
