"""The estate record.

Shape matters here for a reason that is not technical. An executor may have to account for
what was done to a dead person's property, to a family or to a probate court. So the store is
append-only for actions, every discovered asset carries the search that produced it, and
nothing is ever silently overwritten.

Mirrored one-to-one by the Xano tables in docs/XANO.md. This module is the contract; Xano is
the deployment of it.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Kind(str, Enum):
    DOMAIN = "domain"
    PROFILE = "profile"
    BYLINE = "byline"
    LISTING = "listing"
    OBITUARY = "obituary"


class Status(str, Enum):
    """A search result is a candidate until a person says otherwise. Attributing a stranger's
    website to a dead man is a real harm, so nothing acts on PENDING."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Verb(str, Enum):
    DISCOVER = "discover"
    CONFIRM = "confirm"
    REJECT = "reject"
    RENEW = "renew"
    REGISTER = "register"
    DNS_UPDATE = "dns_update"


@dataclass
class Estate:
    subject_name: str                      # the person who died
    executor_email: str
    died_on: str | None = None
    anchors: list[str] = field(default_factory=list)   # city, employer, a known handle
    id: str = field(default_factory=_uid)
    created_at: str = field(default_factory=_now)


@dataclass
class Candidate:
    """Something the search found that might belong to the subject."""
    estate_id: str
    kind: Kind
    label: str
    url: str
    source: str                            # which SerpApi engine and query produced this
    snippet: str = ""
    status: Status = Status.PENDING
    decided_by: str | None = None
    decided_at: str | None = None
    id: str = field(default_factory=_uid)


@dataclass
class Domain:
    estate_id: str
    name: str
    expires_on: str | None = None          # ISO date; None until we have a real record
    registrar: str | None = None
    auto_renew_grace_days: int | None = None
    source: str = "unknown"                # provenance of expires_on -- never presented without it
    last_checked: str | None = None
    id: str = field(default_factory=_uid)


@dataclass(frozen=True)
class Action:
    """Append-only. Never updated, never deleted -- this is the account of what was done."""
    estate_id: str
    verb: Verb
    target: str
    actor: str
    detail: dict
    dry_run: bool
    result: str
    id: str = field(default_factory=_uid)
    at: str = field(default_factory=_now)


class Store:
    """A JSON-backed implementation of the Xano contract, so the console runs with no keys.
    The Xano adapter satisfies the same five methods against the tables in docs/XANO.md."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._db = {"estates": [], "candidates": [], "domains": [], "actions": []}
        if self.path.exists():
            self._db = json.loads(self.path.read_text())

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._db, indent=2, default=str))

    # --- writes ---------------------------------------------------------------
    def add_estate(self, e: Estate) -> Estate:
        self._db["estates"].append(asdict(e)); self._flush(); return e

    def add_candidates(self, cs: Iterable[Candidate]) -> list[Candidate]:
        cs = list(cs)
        seen = {c["url"] for c in self._db["candidates"]}
        fresh = [c for c in cs if c.url not in seen]      # re-running a search must not duplicate
        self._db["candidates"].extend(asdict(c) for c in fresh)
        self._flush()
        return fresh

    def decide(self, candidate_id: str, status: Status, actor: str) -> dict:
        for c in self._db["candidates"]:
            if c["id"] == candidate_id:
                c["status"] = status.value
                c["decided_by"] = actor
                c["decided_at"] = _now()
                self._flush()
                return c
        raise KeyError(candidate_id)

    def upsert_domain(self, d: Domain) -> Domain:
        for row in self._db["domains"]:
            if row["estate_id"] == d.estate_id and row["name"] == d.name:
                row.update({k: v for k, v in asdict(d).items() if k != "id" and v is not None})
                self._flush()
                return d
        self._db["domains"].append(asdict(d)); self._flush(); return d

    def log(self, a: Action) -> Action:
        self._db["actions"].append(asdict(a)); self._flush(); return a

    # --- reads ----------------------------------------------------------------
    def candidates(self, estate_id: str, status: Status | None = None) -> list[dict]:
        rows = [c for c in self._db["candidates"] if c["estate_id"] == estate_id]
        return [c for c in rows if status is None or c["status"] == status.value]

    def domains(self, estate_id: str) -> list[dict]:
        return [d for d in self._db["domains"] if d["estate_id"] == estate_id]

    def actions(self, estate_id: str) -> list[dict]:
        return [a for a in self._db["actions"] if a["estate_id"] == estate_id]

    def estate(self, estate_id: str) -> dict:
        for e in self._db["estates"]:
            if e["id"] == estate_id:
                return e
        raise KeyError(estate_id)
