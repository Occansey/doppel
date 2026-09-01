# Doppel

**Someone is being you, and taking money for it.**

Your customers cannot tell `goodwinplumbing` from `goodwinplurnbing`. Neither can Google.
Doppel finds the lookalike domains impersonating a small business, works out which are already
taken, and tells the owner which three actually matter today.

DevNetwork [API + Cloud + AI] Hackathon 2026 · online track.
Targets three stacking sponsor challenges: **SerpApi**, **Xano**, **name.com**.

---

## The problem

A plumber's customers get scammed by a fake version of his business — same name, same photos,
taking deposits for jobs nobody will turn up to. He finds out when someone shouts at him about
money he never took.

This is solved. It is called brand protection, it costs upward of $10,000 a year, and it is
sold to companies with legal departments. Nobody sells it to a business with four employees
and a van, which is most businesses.

## What it does

**Sweep.** Generate the lookalikes an attacker would actually register — not every
permutation. The dangerous ones are typo-reachable from a phone keyboard, or read correctly at
a glance (`rn` for `m`, `1` for `l`), or sit on a TLD a customer would believe.

**Check.** Ask name.com, in bulk, which of them somebody already owns.

**Rank.** Ask SerpApi who is actually ranking for the business name. A lookalike that is
registered *and* appearing in search is a scam happening today; a free one is a risk you can
close for the price of a callout. Most of the tail is noise, and Doppel says so.

**Defend.** Register the dangerous free ones and point their DNS at the real site, so a
mistyped address still lands the customer where it should.

## Where each API does real work

| | |
|---|---|
| **name.com** | bulk availability → registration → DNS records. Four endpoints, all load-bearing. |
| **SerpApi** | who is ranking for the brand. This is what separates a hypothetical from a live scam. |
| **Xano** | the case file, the triage decisions, and an append-only evidence ledger. |

## The SaaS tool this replaces

Enterprise brand protection — MarkMonitor, ZeroFox and friends. Rebuilt for someone who cannot
justify a five-figure retainer and does not have a legal team to hand the output to.

## What it refuses to do

- **It will not cry wolf.** A free lookalike never reaches an urgent band; a review site that
  ranks for your name is a *mention*, not an impersonator. Both have tests, because the
  failure mode here is a business filing abuse reports against Checkatrade.
- **It does not spend money quietly.** Registration requires an explicit confirmation, and a
  refusal is written to the ledger too.
- **Sandbox by default** (`api.dev.name.com`). Real credentials must be supplied deliberately.
- **Every finding carries its provenance** — fixture or live, and which query produced it.

## Run

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
PYTHONPATH=src ./.venv/bin/python -m pytest tests/ -q
./run.sh      # console on http://localhost:8077
```

Runs on fixtures with no keys, and says so on screen. To go live:

```bash
SERPAPI_KEY=…  NAMECOM_USER=…  NAMECOM_TOKEN=…  XANO_BASE=…
```

See [SPECIFICATION.md](SPECIFICATION.md) for the contract and [docs/XANO.md](docs/XANO.md)
for the schema.
