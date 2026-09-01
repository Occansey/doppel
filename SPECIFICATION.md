# Doppel

**One line:** Small businesses are impersonated on lookalike domains and find out from angry
customers. Doppel finds the lookalikes, ranks them by what is actually happening, and lets the
owner take the dangerous ones away from the attacker.

DevNetwork [API + Cloud + AI] Hackathon 2026 · online · deadline **Sep 3, 2026 19:00 Paris**.

---

## 1. The problem, precisely

An attacker does not need to hack anything. They register a domain one keystroke or one glyph
away from a real business, copy the site, and take deposits. The business has no idea until a
customer complains about money it never received.

Three things make it work:

- `rn` renders as `m`. `1` renders as `l`. `vv` renders as `w`. At a glance, in a browser bar
  or an email, the fake is the real one.
- Customers believe `.com` belongs to you even when your site is `.co.uk`.
- Search will happily rank the impostor for your own business name.

## 2. What the product does

1. **Sweep** — generate the variants an attacker would actually pick, ranked by how well each
   fools a human, capped so the list stays readable.
2. **Check** — bulk availability from name.com: who already owns them.
3. **Rank** — SerpApi: who is ranking for the business name. Registered + ranking = live scam.
4. **Defend** — register the dangerous free ones; point DNS at the real site.

## 3. Where each API is load-bearing

- **name.com** — availability, registration, DNS records. Remove it and there is no product.
- **SerpApi** — the only way to know whether a lookalike is *being used*. Without it every
  finding is hypothetical and the ranking is guesswork.
- **Xano** — case, findings, triage decisions, append-only ledger. If this reaches a registrar
  or a payment processor, the case is only as strong as the record.

## 4. The rules this build holds itself to

- **Never register without an explicit confirmation.** It spends money. Refusals are logged.
- **Never cry wolf.** Free variants cannot reach an urgent band. A host that merely mentions
  the brand is not an impersonator. Both are tested; both were bugs first.
- **Sandbox by default.** `api.dev.name.com` unless deliberately overridden.
- **Provenance on every row.** Fixture or live, and the query that produced it. A console that
  cannot tell you which would let someone file an abuse report against an unchecked domain.
- **The ledger is append-only.** No endpoint updates or deletes an action.

## 5. Not in scope

Filing abuse reports automatically, contacting the impersonator, anything touching the
customer's payment credentials, or taking down content. Doppel produces evidence and takes
domains off the market. A human decides what to do with the rest.
