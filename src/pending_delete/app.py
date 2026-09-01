"""The console: FastAPI in front of the estate store, the clock, and the two outward APIs."""
from __future__ import annotations

import os, re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import adapters
from .lifecycle import assess
from .model import Action, Candidate, Domain, Estate, Kind, Status, Store, Verb

WEB = Path(__file__).resolve().parents[2] / "web"
DATA = Path(__file__).resolve().parents[2] / "data" / "estate.json"

app = FastAPI(title="Pending Delete")
store = Store(DATA)

DOMAINISH = re.compile(r"^https?://([^/]+)")


def _today() -> date:
    # Overridable so the demo is reproducible and the tests are not time-dependent.
    return date.fromisoformat(os.getenv("PD_TODAY", str(date.today())))


@app.get("/", response_class=HTMLResponse)
def console() -> str:
    return (WEB / "console.html").read_text()


@app.get("/api/health")
def health():
    return {"ok": True,
            "serpapi": bool(os.getenv("SERPAPI_KEY")),
            "namecom": bool(os.getenv("NAMECOM_USER") and os.getenv("NAMECOM_TOKEN")),
            "namecom_env": "LIVE" if os.getenv("NAMECOM_LIVE") == "1" else "sandbox",
            "xano": bool(os.getenv("XANO_BASE")),
            "today": str(_today())}


class NewEstate(BaseModel):
    subject_name: str
    executor_email: str
    died_on: str | None = None
    anchors: list[str] = []


@app.post("/api/estate")
def create_estate(body: NewEstate):
    e = store.add_estate(Estate(**body.model_dump()))
    store.log(Action(estate_id=e.id, verb=Verb.DISCOVER, target=e.subject_name,
                     actor=e.executor_email, detail=body.model_dump(), dry_run=True,
                     result="estate opened"))
    return {"estate_id": e.id}


@app.post("/api/estate/{estate_id}/discover")
def discover(estate_id: str):
    e = store.estate(estate_id)
    found = adapters.discover(e["subject_name"], e.get("anchors") or [])
    cands = []
    for r in found.value:
        host = (DOMAINISH.match(r["url"]) or [None, ""])[1].lower().removeprefix("www.")
        kind = Kind.DOMAIN if host and "." in host else Kind.PROFILE
        if r["engine"] == "google_news":
            kind = Kind.OBITUARY
        elif r["engine"] == "google_local":
            kind = Kind.LISTING
        cands.append(Candidate(estate_id=estate_id, kind=kind, label=r["label"], url=r["url"],
                               snippet=r["snippet"], source=f'{found.source} · {r["engine"]}'))
    fresh = store.add_candidates(cands)
    store.log(Action(estate_id=estate_id, verb=Verb.DISCOVER, target=e["subject_name"],
                     actor=e["executor_email"], detail={"found": len(cands), "new": len(fresh)},
                     dry_run=True, result=f"{len(fresh)} new candidates"))
    return {"new": len(fresh), "live": found.live, "source": found.source}


class Decision(BaseModel):
    status: Status
    actor: str


@app.post("/api/candidate/{candidate_id}/decide")
def decide(candidate_id: str, body: Decision):
    c = store.decide(candidate_id, body.status, body.actor)
    if body.status is Status.CONFIRMED and c["kind"] == Kind.DOMAIN.value:
        host = (DOMAINISH.match(c["url"]) or [None, ""])[1].lower().removeprefix("www.")
        reg = adapters.registration(host)
        row = reg.value or {}
        store.upsert_domain(Domain(estate_id=c["estate_id"], name=host,
                                   expires_on=row.get("expires_on"),
                                   registrar=row.get("registrar"), source=reg.source,
                                   last_checked=str(_today())))
    store.log(Action(estate_id=c["estate_id"],
                     verb=Verb.CONFIRM if body.status is Status.CONFIRMED else Verb.REJECT,
                     target=c["url"], actor=body.actor, detail={"candidate": candidate_id},
                     dry_run=False, result=body.status.value))
    return c


@app.get("/api/estate/{estate_id}")
def read(estate_id: str):
    e = store.estate(estate_id)
    today = _today()
    doms = []
    for d in store.domains(estate_id):
        if not d.get("expires_on"):
            doms.append({**d, "phase": "unknown", "days_left": None, "recoverable": None})
            continue
        c = assess(d["name"], date.fromisoformat(d["expires_on"]), today=today,
                   auto_renew_grace_days=d.get("auto_renew_grace_days") or 30,
                   source=d.get("source", "unknown"))
        doms.append({**d, "phase": c.phase.value, "days_left": c.days_left,
                     "recoverable": c.recoverable, "resolves": c.resolves,
                     "unrecoverable_on": str(c.unrecoverable_on)})
    doms.sort(key=lambda x: (x["days_left"] is None, x["days_left"]))
    return {"estate": e, "domains": doms,
            "candidates": store.candidates(estate_id),
            "ledger": list(reversed(store.actions(estate_id)))}


class Hold(BaseModel):
    action: str            # renew | register | dns
    actor: str
    confirm: bool = False
    target_ip: str | None = None


@app.post("/api/domain/{estate_id}/{name}/hold")
def hold(estate_id: str, name: str, body: Hold):
    """The only endpoint that spends money or claims a name. A refusal is logged too --
    a record of what was declined is part of the account an executor may have to give."""
    if not body.confirm:
        store.log(Action(estate_id=estate_id, verb=Verb.RENEW, target=name, actor=body.actor,
                         detail=body.model_dump(), dry_run=True,
                         result="refused: no explicit confirmation"))
        raise HTTPException(400, "This spends money or claims a name. Send confirm=true.")
    verb = {"renew": Verb.RENEW, "register": Verb.REGISTER, "dns": Verb.DNS_UPDATE}[body.action]
    live = bool(os.getenv("NAMECOM_USER") and os.getenv("NAMECOM_TOKEN"))
    result = "would call name.com (no credentials configured)" if not live else "submitted"
    store.log(Action(estate_id=estate_id, verb=verb, target=name, actor=body.actor,
                     detail=body.model_dump(), dry_run=not live, result=result))
    return JSONResponse({"ok": True, "dry_run": not live, "result": result})
