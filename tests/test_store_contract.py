"""Both stores must satisfy the same contract. If they drift, the console silently behaves
differently depending on whether Xano is configured -- exactly the class of bug that only
shows up in the demo."""
import inspect
from doppel.model import Store
from doppel.xano import XanoStore

CONTRACT = ["add_case", "add_findings", "decide", "upsert_held",
            "log", "findings", "held", "actions", "case"]


def test_xano_implements_every_local_method():
    for name in CONTRACT:
        assert hasattr(XanoStore, name), f"XanoStore is missing {name}"
        assert hasattr(Store, name), f"Store is missing {name}"


def test_signatures_match():
    for name in CONTRACT:
        a = inspect.signature(getattr(Store, name))
        b = inspect.signature(getattr(XanoStore, name))
        assert list(a.parameters)[1:] == list(b.parameters)[1:], f"{name} signatures differ"


def test_actions_table_has_no_mutating_methods():
    """Append-only is a property of the design, not a convention. Nothing may edit history."""
    for cls in (Store, XanoStore):
        names = [n for n in dir(cls) if not n.startswith("_")]
        assert not [n for n in names if "delete" in n or "update_action" in n]


def test_findings_dedupe_per_case_not_globally(tmp_path):
    """A second case for the same business must still get its findings. Deduping on url
    alone made the store disagree with the unique index documented for Xano."""
    from doppel.model import Store, Case, Finding, Kind
    st = Store(tmp_path / "s.json")
    a = st.add_case(Case(business_name="A", domain="a.com", owner_email="x@y.z"))
    b = st.add_case(Case(business_name="A again", domain="a.com", owner_email="x@y.z"))
    mk = lambda cid: [Finding(case_id=cid, kind=Kind.LOOKALIKE, label="a1.com",
                              url="https://a1.com", source="t")]
    assert len(st.add_findings(mk(a.id))) == 1
    assert len(st.add_findings(mk(b.id))) == 1      # different case: not a duplicate
    assert len(st.add_findings(mk(a.id))) == 0      # same case: correctly deduped
