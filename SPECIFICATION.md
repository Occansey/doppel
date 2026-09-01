# Pending Delete

**One line:** When someone dies, their domain walks the ICANN deletion lifecycle alone — and
about seventy-five days later their life's work is released to a drop-catcher. This is the
executor's console that races that clock.

DevNetwork [API + Cloud + AI] Hackathon 2026 · online track · deadline **Sep 3, 2026 10:00 PDT**
(19:00 Paris). Targets three stacking sponsor challenges: **SerpApi**, **Xano**, **name.com**.

---

## 1. The problem, precisely

A domain does not vanish when it expires. It walks a defined lifecycle, and every phase has a
name written into ICANN policy:

| phase | typical length | what the family sees |
|---|---|---|
| Active | — | the site works |
| **Auto-Renew Grace Period** | ~30 days after expiry | usually still resolves; nobody notices |
| **Redemption Grace Period** | 30 days | **the site goes dark**; restore still possible, for a fee |
| **Pending Delete** | 5 days | cannot be restored by anyone, at any price |
| Released | — | available to the public; valuable names are taken within seconds |

The cruelty is the ordering. The site stays up through the phase where recovery is cheap, and
goes dark at the exact moment recovery becomes expensive. Families notice on roughly day 30 —
inside Redemption — and have about 35 days left, which nobody tells them.

Meanwhile the executor does not know: which registrar, which email the renewal notice goes to,
what else the person had online, or that a clock is running at all.

## 2. What the product does

Three moves, in order.

**Find.** Given a name and a few anchors (city, employer, a known handle), discover the
person's public footprint — sites, bylines, business listings, profiles, obituaries. The
family almost never has the full list.

**Time.** For every domain found, read its real registration record and place it on the
lifecycle above with a dated deadline: *this becomes unrecoverable on 14 November.*

**Hold.** Renew what must be kept. For what is already lost, secure the name before a
drop-catcher does. Repoint DNS so the address resolves to a memorial page rather than nothing —
or, later, to whatever the family chooses.

## 3. Where each API does real work

- **SerpApi** — the Find step. Live structured search across web, news, and local results to
  assemble the footprint from fragments. Nothing else can do this from a name and a city.
- **name.com** — the Time and Hold steps. Not one call: availability *and* registration *and*
  DNS record management, plus reading expiry to drive the lifecycle clock.
- **Xano** — the system of record and the workflow: estate, executor identity, discovered
  assets, the phase clock, every action written to an audit trail an executor may have to
  show a probate court.

## 4. The SaaS tool this replaces

Registrar account recovery for a deceased holder. Today that is a PDF, a death certificate
scan, an email queue, and six weeks — repeated separately at every registrar, while the clock
in §1 keeps running. It is the worst software anyone touches on the worst week of their life.

## 5. Rules this build holds itself to

- **Never register or renew anything without an explicit human confirmation.** The product
  spends money and claims names. Every write is confirmed, shown in full first, and logged.
- **Sandbox by default.** `api.dev.name.com` unless real credentials are deliberately supplied.
- **A date is a claim.** Every deadline shown must be derived from a real registration record
  and labelled with where it came from. No estimated dates presented as certain.
- **Discovery is evidence, not proof.** A search result is a candidate until a human confirms
  it belongs to the person. Wrong attribution here is a real harm.
- **No death certificates, no identity documents, no payment details** are handled by this
  build. It is a clock and a console, not a probate service.

## 6. Not in scope

Probate law, executor legal authority verification, transferring registrar ownership,
handling the deceased's email, or anything touching bank or payment credentials.
