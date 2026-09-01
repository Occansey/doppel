"""Turn a confirmed impersonation into something a registrar will act on.

Finding the fake is the easy half. The business then has to convince somebody with the power
to switch it off, and abuse desks reject vague complaints for a living. What they act on is
specific: the exact domain, the exact evidence, the date it was observed, and what the
complainant actually wants done.

Doppel does not send anything. It assembles the case and hands it over -- the decision to
accuse someone stays with a person.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Report:
    subject: str
    body: str
    evidence_count: int
    ready: bool
    missing: list[str]


def _stamp(iso: str | None) -> str:
    if not iso:
        return "date not recorded"
    return iso.replace("T", " ")[:16] + " UTC"


def build(*, case: dict, finding: dict, ledger: list[dict]) -> Report:
    """Assemble an abuse report from the case file. Refuses to look finished when it is not:
    a confident-looking report built on a fixture lookup would be worse than no report."""
    missing: list[str] = []
    src = (finding.get("source") or "")
    if "fixture" in src:
        missing.append("availability was read from a fixture, not a live registry lookup")
    if finding.get("registered") is not True:
        missing.append("this domain is not registered by anyone — there is no party to report")
    if finding.get("status") != "hostile":
        missing.append("nobody has confirmed this is hostile")

    # Every ledger line that touches this domain is evidence of when it was observed.
    evidence = [a for a in ledger if a.get("target") == finding.get("label")]
    observed = sorted(a.get("at", "") for a in evidence)
    first_seen = _stamp(observed[0] if observed else None)

    # Only claim what the record supports. The earlier draft asserted that customers had
    # been defrauded -- a sentence nobody had evidenced, put in the business owner's mouth,
    # in a document that ends by saying nothing is asserted beyond the record.
    ranking = "ranking" in src or finding.get("risk", 0) >= 85
    harm_lines = ["  The domain is registered to someone other than us and imitates our name."]
    if ranking:
        harm_lines.append("  It appears in search results for our business name, so customers "
                          "looking for us are shown it.")
    harm = "\n".join(harm_lines)

    body = f"""To: the abuse team at the registrar of record

Domain complained of: {finding.get('label')}
Complainant: {case.get('business_name')} ({case.get('domain')})
Contact: {case.get('owner_email')}
First observed: {first_seen}

We operate {case.get('domain')}. The domain above is a deliberate imitation of it.

How it imitates us
  Technique: {finding.get('technique')}
  {finding.get('snippet') or ''}

Why this causes harm
{harm}

What we are asking for
  Suspension of {finding.get('label')} under your acceptable use policy, and preservation of
  registration records pending any further action.

Record of observation
{chr(10).join(f"  {_stamp(a.get('at'))}  {a.get('verb')}  {a.get('result')}" for a in evidence) or '  (no observations recorded yet)'}

Assembled by Doppel from a case file. Every line above is drawn from a recorded observation;
nothing is asserted that is not in the record.
"""
    return Report(subject=f"Abuse report: {finding.get('label')} impersonating {case.get('domain')}",
                  body=body, evidence_count=len(evidence),
                  ready=not missing, missing=missing)
