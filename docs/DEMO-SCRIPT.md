# Demo script — Doppel

**Length:** 2:00–2:30. The challenges ask for 2–4 minutes; shorter and sharper wins.
**Record on this machine** — its IP is allowlisted with name.com, so the whole pipeline is live.
The deployed URL cannot do availability lookups and says so.

**Before you hit record**
1. `./run.sh` — console on http://localhost:8077
2. Clear the case: in the browser console, `localStorage.removeItem('doppel_case')`, reload.
3. Confirm the ticker reads **serpapi LIVE · name.com LIVE · store XanoStore**. If any says
   FIXTURE, stop — the demo is worthless without it.
4. Run one sweep before recording, so a second sweep during the video populates "what changed".

---

## 0 · 0:00–0:18 — the problem

**On screen:** the headline, full width.

> A plumber in London gets a phone call. A customer is furious about a two-hundred-pound
> deposit. He never took it. Somebody registered a domain one letter away from his, copied his
> site, and has been taking his customers' money for a month.

## 1 · 0:18–0:35 — why nobody solves it for him

> This is a solved problem. It's called brand protection, it starts around ten thousand a year,
> and it's sold to companies with legal departments. Nobody sells it to a man with four
> employees and a van.

## 2 · 0:35–1:00 — the sweep

**ACTION:** Click **RUN SWEEP**. Takes about ten seconds.

> Doppel generates the lookalikes an attacker would actually pick — one key away on a phone,
> or ones that fool the eye. R-N reads as M. One reads as L. Then it asks name.com, in bulk,
> which of these somebody already owns.

## 3 · 1:00–1:30 — the part that matters

**On screen:** point at **ALREADY YOURS 04**.

> Six of these are registered. Five of them redirect to Pimlico's own site — they bought them
> defensively years ago. A tool that alarmed on all six would be wrong five times out of six,
> and a business that gets cried wolf at once stops opening the emails.
>
> So Doppel follows every registered lookalike to see where it actually goes. Four dismissed.

**ACTION:** Point at `pimlicoplumbersfranchise.co.uk`, risk 74.

> This one uses the name and ranks in search — and it's their own franchise site. A sub-brand
> and an impersonator are identical as strings. So it isn't accused; it's flagged, and it says
> "check this is yours."

## 4 · 1:30–1:50 — the AI, and what it isn't allowed to do

**ACTION:** Click **LOOK AT IT** on that row.

> Rules can't tell those apart, so a model reads both pages. Two things it cannot do: it can
> never raise the severity — it only recommends — and a verdict with no quoted evidence is
> thrown away. This ends up in an abuse report a registrar will read.

## 5 · 1:50–2:10 — turning it into action

**ACTION:** Mark a registered one **HOSTILE**, then click **ABUSE REPORT**.

> Finding the fake is the easy half. Abuse desks reject vague complaints for a living. Doppel
> assembles the case from the ledger — the domain, the technique, dated observations, a clear
> ask — and it refuses to look finished if it isn't. Doppel never sends it. Accusing someone
> stays a human decision.

## 6 · 2:10–2:25 — close

**ACTION:** Scroll so the ticker and the URL are visible.

> SerpApi for who's really ranking. name.com for availability, registration and DNS. Xano for
> the case file and an append-only ledger. And a public deployment that deliberately cannot
> spend your money.

---

## Do not say
- "It finds scammers" — it finds *candidates* and refuses to accuse.
- Any claim that a specific named business is fraudulent. Every real domain in this demo turned
  out to be legitimate. That is the point of the demo, not a weakness in it.
