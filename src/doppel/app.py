"""Doppel — the console."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import adapters, destination as dest, report, triage
from .model import Action, Case, Finding, Held, Kind, Status, Verb
from .variants import generate
from .xano import open_store

WEB = Path(__file__).resolve().parents[2] / "web"
DATA = Path(__file__).resolve().parents[2] / "data" / "doppel.json"

app = FastAPI(title="Doppel")
store = open_store(DATA)


@app.get("/")
def console():
    from fastapi.responses import HTMLResponse
    return HTMLResponse((WEB / "console.html").read_text())


@app.get("/api/health")
def health():
    return {"ok": True,
            "serpapi": bool(os.getenv("SERPAPI_KEY")),
            "namecom": bool(os.getenv("NAMECOM_USER") and os.getenv("NAMECOM_TOKEN")),
            "namecom_env": "LIVE" if os.getenv("NAMECOM_LIVE") == "1" else "sandbox",
            "xano": bool(os.getenv("XANO_BASE")),
            "store": type(store).__name__}


class NewCase(BaseModel):
    business_name: str
    domain: str
    owner_email: str
    anchors: list[str] = []


@app.post("/api/case")
def create_case(b: NewCase):
    c = store.add_case(Case(**b.model_dump()))
    store.log(Action(case_id=c.id, verb=Verb.SWEEP, target=c.domain, actor=c.owner_email,
                     detail=b.model_dump(), dry_run=True, result="case opened"))
    return {"case_id": c.id}


@app.post("/api/case/{case_id}/sweep")
def sweep(case_id: str, limit: int = 60):
    """Generate variants, ask name.com who owns them, ask SerpApi who is ranking, score."""
    c = store.case(case_id)
    variants = generate(c["domain"], limit=limit)
    avail = adapters.availability([v.domain for v in variants])
    ranking = adapters.who_ranks(c["business_name"], c.get("anchors") or [], c["domain"])
    ranked_hosts = {h["host"] for h in ranking.value}

    findings = []
    for v in variants:
        reg = avail.value.get(v.domain, {}).get("registered")
        is_ranking = v.domain in ranked_hosts
        # Only registered domains are worth following -- a free one has nowhere to go, and
        # the check costs a request each.
        d = dest.classify(v.domain, c["domain"]) if reg else None
        s = triage.score(technique=v.technique, registered=reg, ranking=is_ranking,
                         resolves=is_ranking, destination=d.verdict if d else None)
        findings.append(Finding(
            case_id=case_id, kind=Kind.LOOKALIKE, label=v.domain,
            url=f"https://{v.domain}", snippet=v.why, technique=v.technique,
            registered=reg, risk=s,
            source=f"{avail.source}" + (f" · ranking: {ranking.source}" if is_ranking else "")))

    # Anything ranking for the brand that is not a generated variant: an impostor we would
    # never have guessed. This is the case for live search rather than a wordlist.
    for h in ranking.value:
        if h["host"] in {v.domain for v in variants} or h["host"] == c["domain"]:
            continue
        risk, technique = triage.rank_finding_score(h["host"], c["domain"])
        findings.append(Finding(
            case_id=case_id, kind=Kind.IMPOSTOR, label=h["host"], url=h["url"],
            snippet=h["snippet"], technique=technique, registered=True, risk=risk,
            source=f'{ranking.source} · position {h.get("position")}'))

    fresh = store.add_findings(findings)
    store.log(Action(case_id=case_id, verb=Verb.SWEEP, target=c["domain"], actor=c["owner_email"],
                     detail={"variants": len(variants), "new": len(fresh),
                             "availability_live": avail.live, "search_live": ranking.live},
                     dry_run=True,
                     result=f"{len(fresh)} findings ({avail.source}; {ranking.source})"))
    return {"new": len(fresh), "availability_live": avail.live, "search_live": ranking.live}


class Triage(BaseModel):
    status: Status
    actor: str


@app.post("/api/finding/{finding_id}/triage")
def do_triage(finding_id: str, b: Triage):
    f = store.decide(finding_id, b.status, b.actor)
    store.log(Action(case_id=f["case_id"], verb=Verb.TRIAGE, target=f["label"], actor=b.actor,
                     detail={"finding": finding_id}, dry_run=False, result=b.status.value))
    return f


class Defend(BaseModel):
    actor: str
    confirm: bool = False
    redirect_to: str | None = None


@app.post("/api/case/{case_id}/defend/{domain}")
def defend(case_id: str, domain: str, b: Defend):
    """Register a dangerous free lookalike and point it at the real site. The only endpoint
    that spends money. A refusal is logged too -- the record of what was declined matters."""
    if not b.confirm:
        store.log(Action(case_id=case_id, verb=Verb.DEFEND, target=domain, actor=b.actor,
                         detail=b.model_dump(), dry_run=True,
                         result="refused: no explicit confirmation"))
        raise HTTPException(400, "This spends money. Send confirm=true.")
    reg = adapters.register(domain)
    store.log(Action(case_id=case_id, verb=Verb.DEFEND, target=domain, actor=b.actor,
                     detail={"years": 1}, dry_run=not reg.live, result=reg.source))
    dns = None
    if b.redirect_to:
        dns = adapters.redirect(domain, b.redirect_to)
        store.log(Action(case_id=case_id, verb=Verb.REDIRECT, target=domain, actor=b.actor,
                         detail={"cname": b.redirect_to}, dry_run=not dns.live, result=dns.source))
    store.upsert_held(Held(case_id=case_id, name=domain, redirects_to=b.redirect_to,
                           source=reg.source))
    return {"registered": reg.value, "dns": dns.value if dns else None, "live": reg.live}


@app.get("/api/case/{case_id}")
def read(case_id: str):
    fs = sorted(store.findings(case_id), key=lambda f: -f.get("risk", 0))
    for f in fs:
        f["band"] = triage.band(f.get("risk", 0))
        f["advice"] = triage.advice(registered=f.get("registered"),
                                    ranking="ranking" in (f.get("source") or ""),
                                    technique=f.get("technique", ""))
    return {"case": store.case(case_id), "findings": fs,
            "held": store.held(case_id), "ledger": list(reversed(store.actions(case_id)))}


@app.get("/api/finding/{finding_id}/report")
def abuse_report(finding_id: str):
    """Assemble the registrar abuse report. Doppel never sends it -- the decision to accuse
    someone stays with a person, and the report says plainly what is still missing."""
    for f in store._db["findings"] if hasattr(store, "_db") else []:
        if f["id"] == finding_id:
            c = store.case(f["case_id"])
            r = report.build(case=c, finding=f, ledger=store.actions(f["case_id"]))
            return {"subject": r.subject, "body": r.body, "ready": r.ready,
                    "missing": r.missing, "evidence": r.evidence_count}
    raise HTTPException(404, "no such finding")
