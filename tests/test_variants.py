import pytest
from doppel.variants import generate, typos, glyphs, Variant

D = "goodwinplumbing.co.uk"


def names(vs): return [v.domain for v in vs]


def test_the_classic_homoglyph_is_found_and_ranked_first():
    """rn/m is how this attack has worked for twenty years. If it is not near the top,
    the ranking is wrong."""
    vs = generate(D)
    assert "goodwinplurnbing.co.uk" in names(vs)
    assert vs[0].technique == "reads the same"


def test_believable_tlds_keep_the_exact_name():
    vs = names(generate(D))
    assert "goodwinplumbing.com" in vs
    assert "goodwinplumbing.shop" in vs


def test_never_returns_the_domain_being_protected():
    assert D not in names(generate(D))


def test_no_duplicates():
    vs = names(generate(D))
    assert len(vs) == len(set(vs))


def test_every_variant_explains_itself():
    """A case file listing 40 domains is worth less than one saying why each is a risk."""
    for v in generate(D):
        assert v.why and v.why[0].isupper() and v.why.endswith(".")


def test_limit_is_honoured_because_every_entry_costs_a_live_lookup():
    assert len(generate(D, limit=10)) == 10


def test_typos_cover_the_four_real_error_shapes():
    ts = {t for _, t in typos("abc")}
    assert ts == {"fat finger", "dropped character", "transposed", "doubled character"}


def test_glyph_substitution_is_bidirectional():
    assert any(n == "rnilk" for n, _ in glyphs("milk"))     # m -> rn
    assert any(n == "milk" for n, _ in glyphs("rnilk"))     # rn -> m


def test_malformed_input_is_rejected_not_guessed():
    with pytest.raises(ValueError):
        generate("nodothere")
