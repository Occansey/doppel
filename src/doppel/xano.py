"""Xano as the system of record.

Satisfies the same methods as `model.Store`, so the console does not know which is behind it.
That is what writing the contract first bought: Xano is a deployment of the schema in
docs/XANO.md, not something the application was bent around.

Rows are addressed through Xano's table content API. The workspace and table ids come from
XANO_WORKSPACE / XANO_TABLES so the same code runs against a different workspace unchanged.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from typing import Iterable

import httpx

from .model import Action, Case, Finding, Held, Status

DEFAULT_TABLES = {"cases": 885041, "findings": 885042, "held": 885043, "actions": 885044}


def _token() -> str | None:
    tok = os.getenv("XANO_TOKEN")
    if tok:
        return tok
    # Fall back to the CLI's credentials file so the app works wherever `xano profile` ran.
    path = os.path.expanduser("~/.xano/credentials.yaml")
    if not os.path.exists(path):
        return None
    for line in open(path):
        if "access_token:" in line:
            return line.split("access_token:", 1)[1].strip()
    return None


class XanoStore:
    def __init__(self, origin: str | None = None, workspace: int | None = None):
        self.origin = (origin or os.getenv("XANO_ORIGIN")
                       or "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")
        self.workspace = int(workspace or os.getenv("XANO_WORKSPACE", "168087"))
        self.tables = json.loads(os.getenv("XANO_TABLES", "{}")) or DEFAULT_TABLES
        tok = _token()
        if not tok:
            raise RuntimeError("no Xano token (XANO_TOKEN or ~/.xano/credentials.yaml)")
        self._c = httpx.Client(timeout=30, headers={"Authorization": f"Bearer {tok}",
                                                    "content-type": "application/json"})

    def _base(self, table: str) -> str:
        return f"{self.origin}/api:meta/workspace/{self.workspace}/table/{self.tables[table]}/content"

    def _call(self, method: str, url: str, **kw):
        """Xano's Metadata API rate-limits hard: a sweep inserting rows one at a time returns
        429 partway through and loses the tail. Retry with backoff, and prefer _insert_many."""
        for attempt in range(5):
            r = getattr(self._c, method)(url, **kw)
            if r.status_code != 429:
                r.raise_for_status()
                return r.json()
            time.sleep(2 ** attempt)
        r.raise_for_status()

    def _insert(self, table: str, row: dict) -> dict:
        return self._call("post", self._base(table), json=row)

    def _insert_many(self, table: str, rows: list[dict]) -> list:
        """One request for the whole batch. Forty findings as forty inserts exhausts the
        rate limit; as one bulk call it is a single request."""
        if not rows:
            return []
        out = []
        for i in range(0, len(rows), 100):
            out.extend(self._call("post", f"{self._base(table)}/bulk",
                                  json={"items": rows[i:i + 100]}) or [])
        return out

    def _rows(self, table: str) -> list[dict]:
        out, page = [], 1
        while True:
            d = self._call("get", self._base(table), params={"page": page, "per_page": 200})
            out.extend(d.get("items", []))
            if not d.get("nextPage"):
                return out
            page = d["nextPage"]

    def _patch(self, table: str, row_id: int, row: dict) -> dict:
        return self._call("put", f"{self._base(table)}/{row_id}", json=row)

    # --- writes ---------------------------------------------------------------
    def add_case(self, e: Case) -> Case:
        d = asdict(e)
        self._insert("cases", {"case_id": d["id"], "business_name": d["business_name"],
                               "domain": d["domain"], "owner_email": d["owner_email"],
                               "anchors": json.dumps(d.get("anchors") or []),
                               "created_at_iso": d["created_at"]})
        return e

    def add_findings(self, cs: Iterable[Finding]) -> list[Finding]:
        cs = list(cs)
        if not cs:
            return []
        # Deduped on (case_id, url), matching the unique index in docs/XANO.md.
        seen = {(r.get("case_id"), r.get("url")) for r in self._rows("findings")}
        fresh = [c for c in cs if (c.case_id, c.url) not in seen]
        rows = []
        for c in fresh:
            d = asdict(c)
            rows.append({
                "finding_id": d["id"], "case_id": d["case_id"], "kind": getattr(d["kind"], "value", d["kind"]),
                "label": d["label"], "url": d["url"], "source": d["source"],
                "snippet": d["snippet"], "technique": d["technique"],
                "registered": "" if d["registered"] is None else str(d["registered"]).lower(),
                "risk": int(d["risk"]), "status": getattr(d["status"], "value", d["status"]),
                "decided_by": d["decided_by"] or "", "decided_at": d["decided_at"] or ""})
        self._insert_many("findings", rows)
        return fresh

    def decide(self, finding_id: str, status: Status, actor: str) -> dict:
        from .model import _now
        for r in self._rows("findings"):
            if r.get("finding_id") == finding_id:
                self._patch("findings", r["id"], {**r, "status": status.value,
                                                  "decided_by": actor, "decided_at": _now()})
                return self._shape_finding({**r, "status": status.value})
        raise KeyError(finding_id)

    def upsert_held(self, d: Held) -> Held:
        row = asdict(d)
        for r in self._rows("held"):
            if r.get("case_id") == d.case_id and r.get("name") == d.name:
                self._patch("held", r["id"], {**r, "redirects_to": row["redirects_to"] or "",
                                              "source": row["source"]})
                return d
        self._insert("held", {"held_id": row["id"], "case_id": row["case_id"],
                              "name": row["name"], "redirects_to": row["redirects_to"] or "",
                              "source": row["source"], "acquired_at": row["acquired_at"] or ""})
        return d

    def log(self, a: Action) -> Action:
        # Append-only: nothing in this class updates or deletes an action.
        d = asdict(a)
        self._insert("actions", {"action_id": d["id"], "case_id": d["case_id"],
                                 "verb": getattr(d["verb"], "value", d["verb"]), "target": d["target"],
                                 "actor": d["actor"], "detail": json.dumps(d["detail"]),
                                 "dry_run": str(d["dry_run"]).lower(), "result": d["result"],
                                 "at": d["at"]})
        return a

    # --- reads ----------------------------------------------------------------
    @staticmethod
    def _shape_finding(r: dict) -> dict:
        reg = r.get("registered")
        return {**r, "id": r.get("finding_id"),
                "registered": None if reg in ("", None) else reg == "true",
                "risk": r.get("risk") or 0}

    def findings(self, case_id: str, status: Status | None = None) -> list[dict]:
        rows = [self._shape_finding(r) for r in self._rows("findings")
                if r.get("case_id") == case_id]
        return [r for r in rows if status is None or r["status"] == status.value]

    def held(self, case_id: str) -> list[dict]:
        return [r for r in self._rows("held") if r.get("case_id") == case_id]

    def actions(self, case_id: str) -> list[dict]:
        rows = [r for r in self._rows("actions") if r.get("case_id") == case_id]
        for r in rows:
            r["dry_run"] = r.get("dry_run") == "true"
        return sorted(rows, key=lambda r: r.get("at") or "")

    def case(self, case_id: str) -> dict:
        for r in self._rows("cases"):
            if r.get("case_id") == case_id:
                return {**r, "id": r["case_id"],
                        "anchors": json.loads(r.get("anchors") or "[]")}
        raise KeyError(case_id)


def open_store(local_path):
    """Xano when configured, the local JSON store otherwise. The console reports which."""
    from .model import Store
    if os.getenv("XANO_BASE") or os.getenv("XANO_WORKSPACE"):
        try:
            return XanoStore()
        except Exception:
            return Store(local_path)
    return Store(local_path)
