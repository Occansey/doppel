# Pending Delete

**When someone dies, their domain walks the ICANN deletion lifecycle alone — and about
seventy-five days later their life's work is released to a drop-catcher. This is the
executor's console that races that clock.**

DevNetwork [API + Cloud + AI] Hackathon 2026 · online track.
Targets three stacking sponsor challenges: **SerpApi**, **Xano**, **name.com**.

---

## The clock nobody tells the family about

A domain does not disappear on its expiry date. It walks a defined lifecycle, and every phase
below is a real term in ICANN policy:

| phase | length | site up? | recoverable? |
|---|---|---|---|
| Active | — | yes | yes |
| Auto-Renew Grace | ~30 days | **yes** | yes, cheaply |
| Redemption Grace | 30 days | **no** | yes, for a restore fee |
| Pending Delete | 5 days | no | **no — at any price** |
| Released | — | no | no; often gone in seconds |

The cruelty is the ordering. The site stays up through the phase where recovery is cheap, and
goes dark at the exact moment recovery becomes expensive. Families notice around day 30 —
already inside Redemption — with roughly 35 days left and nobody counting them down.

## What it does

**Find** — the person's public footprint, assembled from a name and a couple of anchors.
**Time** — every domain placed on the lifecycle above, with a dated point of no return.
**Hold** — renew what can be saved, secure what was lost before a drop-catcher takes it,
and repoint DNS to a memorial rather than nothing.

## Where each API does real work

| | |
|---|---|
| **SerpApi** | the Find step — live web, news and local results assembled into a footprint |
| **name.com** | the Time and Hold steps — expiry, availability, registration, DNS |
| **Xano** | estate record, executor identity, the phase clock, and the audit trail |

## Rules this build holds itself to

- Nothing is registered or renewed without an explicit human confirmation, shown in full first.
- Sandbox (`api.dev.name.com`) by default. Real credentials must be supplied deliberately.
- Every date carries its provenance. No estimate is ever presented as a certainty.
- A search result is a *candidate* until a person confirms it. Attributing a stranger's site
  to a dead man is a real harm.
- No death certificates, identity documents, or payment details are handled here.

See [SPECIFICATION.md](SPECIFICATION.md) for the contract.

## Run

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
PYTHONPATH=src ./.venv/bin/python -m pytest tests/ -q
```
