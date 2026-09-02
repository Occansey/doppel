# Devpost submission — copy and paste

**Project:** Doppel
**Tagline:** Someone is being you, and taking money for it.

**Links**
- Repo: https://github.com/Occansey/doppel
- Live: https://doppel-468826425509.us-central1.run.app
- Video: (paste after upload)

---

## The story

A plumber's customers get scammed by a fake version of his business — same name, same photos,
taking deposits for jobs nobody will turn up to. He finds out when someone shouts at him about
money he never took.

This is a solved problem. It is called brand protection, it costs upward of $10,000 a year, and
it is sold to companies with legal departments. Nobody sells it to a business with four
employees and a van, which is most businesses.

Doppel does four things. It **generates** the lookalikes an attacker would actually register —
not every permutation, but the ones that are typo-reachable on a phone keyboard, or read
correctly at a glance (`rn` for `m`, `1` for `l`), or sit on a TLD a customer would believe. It
**checks**, in bulk, which of them somebody already owns. It **follows** each registered one to
see where it really goes. And it **ranks** what is left by what is actually happening.

## What makes it different: it refuses to cry wolf

Generating typosquats is a first-year exercise. Every entry in this challenge will have that.
The hard part is not drowning the owner in false alarms, and this was learned the hard way
against live data:

- A sweep of Pimlico Plumbers found **six registered lookalikes**. Following each one showed
  **five redirect to the real site** — they are Pimlico's own defensive registrations. A tool
  that alarmed on all six would be wrong five times out of six.
- `pimlicoplumbersfranchise.co.uk` scored 100 "live scam" in an early build. It is Pimlico's own
  franchise site. A sub-brand and an impersonator are string-identical, so the rules were changed
  to stop guessing: a search hit can never be auto-labelled a scam.
- Wikipedia, Trustpilot, gov.uk, the BBC and LinkedIn all rank for the brand. None are flagged.
- name.com omits `purchasable` both for taken domains **and** for rows it did not resolve in a
  large batch. Reading absence as "registered" reported **33 free domains as held by attackers**.
  Ambiguous rows are now re-queried before any conclusion is drawn.

Each of those is a test named after the failure.

## Where each API does real work

**name.com** — four endpoints, all load-bearing: bulk availability across ~60 variants,
registration, DNS records to point a recovered lookalike back at the real site, and the
registration record itself. Remove it and there is no product.

**SerpApi** — who is *actually ranking* for the business name. This is the difference between a
hypothetical lookalike and a scam in progress, and nothing else answers it.

**Xano** — the case file: `cases`, `findings`, `held`, `actions`. Schema built through the
Metadata API, writes batched through `/content/bulk` after single inserts hit the rate limit.
The ledger is append-only, because if this reaches a registrar the case is only as strong as
the record.

## The AI

`assessor.py` fills the exact gap the rules refuse to fill. Rules cannot tell a franchise from
an impersonator, so the model reads both pages and judges. Two constraints are enforced rather
than hoped for: **it can never raise a finding's severity** — it recommends to a human — and a
verdict with **no quoted evidence is discarded**, because its output feeds an abuse report a
registrar will read.

## Honest limits

- The name.com API allowlists by IP. The deployed instance is not on the list, so it says
  "name.com UNREACHABLE from this host — availability unknown" rather than showing blanks as
  answers. The full pipeline runs on an allowlisted machine; the video shows that.
- The dev sandbox is not provisioned on this account, so reads run against production and
  **writes are hard-blocked** unless `DOPPEL_ALLOW_SPEND=1`. The deployed image does not set it:
  the public URL cannot spend money, and returns 409 with the reason if asked.
- Doppel never sends the abuse report and never contacts the impersonator. It assembles evidence
  and takes domains off the market. A human decides the rest.

## Build story (Xano challenge)

See `docs/BUILD-STORY.md`. Replaced: enterprise brand protection. Built with Claude Code in
about two working days, including a full pivot from an earlier idea that failed the
"would anyone buy this" test. What AI did not do was decide what to build — that took a human
saying the first idea was wrong.
