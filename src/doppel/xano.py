"""Xano as the system of record.

Satisfies the same methods as `model.Store`, so the console does not know or care which is
behind it. That is the point of writing the contract first: Xano is a deployment of the schema
in docs/XANO.md, not a thing the application code is bent around.

Set XANO_BASE (the workspace API group URL) and optionally XANO_TOKEN to switch over. Absent
those, the app keeps the local JSON store and says so on screen.
"""
from __future__ import annotations

import os
from dataclasses import asdict
from typing import Iterable

import httpx

from .model import Action, Finding, Held, Case, Status


class XanoStore:
    def __init__(self, base: str | None = None, token: str | None = None, timeout: float = 20):
        self.base = (base or os.getenv("XANO_BASE", "")).rstrip("/")
        self.token = token or os.getenv("XANO_TOKEN")
        if not self.base:
            raise RuntimeError("XANO_BASE is not set")
        self._c = httpx.Client(timeout=timeout, headers=self._headers())

    def _headers(self) -> dict:
        h = {"content-type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _post(self, path: str, body: dict) -> dict:
        r = self._c.post(f"{self.base}{path}", json=body)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str, params: dict | None = None):
        r = self._c.get(f"{self.base}{path}", params=params or {})
        r.raise_for_status()
        return r.json()

    # --- writes ---------------------------------------------------------------
    def add_case(self, e: Case) -> Case:
        self._post("/case", asdict(e))
        return e

    def add_findings(self, cs: Iterable[Finding]) -> list[Finding]:
        cs = list(cs)
        if not cs:
            return []
        # The unique index on (case_id, url) makes this idempotent server-side; Xano returns
        # the rows it actually inserted so re-running discovery cannot duplicate a candidate.
        out = self._post(f"/case/{cs[0].case_id}/findings",
                         {"findings": [asdict(c) for c in cs]})
        inserted = {r["url"] for r in out.get("inserted", [])}
        return [c for c in cs if c.url in inserted]

    def decide(self, candidate_id: str, status: Status, actor: str) -> dict:
        return self._post(f"/finding/{candidate_id}/decide",
                          {"status": status.value, "actor": actor})

    def upsert_held(self, d: Held) -> Held:
        self._post("/domain", asdict(d))
        return d

    def log(self, a: Action) -> Action:
        # actions is append-only: Xano exposes no update or delete on this table.
        self._post("/action", asdict(a))
        return a

    # --- reads ----------------------------------------------------------------
    def findings(self, case_id: str, status: Status | None = None) -> list[dict]:
        p = {"status": status.value} if status else None
        return self._get(f"/case/{case_id}/findings", p)

    def held(self, case_id: str) -> list[dict]:
        return self._get(f"/case/{case_id}/domains")

    def actions(self, case_id: str) -> list[dict]:
        return self._get(f"/case/{case_id}/ledger")

    def case(self, case_id: str) -> dict:
        return self._get(f"/case/{case_id}")


def open_store(local_path):
    """Xano when configured, the local JSON store otherwise. The console reports which."""
    from .model import Store
    if os.getenv("XANO_BASE"):
        return XanoStore()
    return Store(local_path)
