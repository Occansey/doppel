# Working in this repository

Read `SPECIFICATION.md` first. It is the contract; this file is how we honour it.

This is **Doppel** — it finds the lookalike domains impersonating a small business, works out
which are already taken, and says which handful matter today. DevNetwork [API + Cloud + AI]
2026, targeting the SerpApi, Xano and name.com challenges.

---

## 1. The failure mode is a false accusation

A missed lookalike costs the business a domain. A wrong one costs it a relationship, an abuse
report against its own review site, or a defamation problem. So every default resolves toward
*ask a human*, never *accuse*.

This is not theoretical. Every one of these shipped and had to be fixed:

- Every host ranking for the brand scored 100 "live scam" — including Checkatrade.
- `pimlicoplumbersfranchise.co.uk` scored 100. It is Pimlico's own franchise site.
- 33 free domains were reported as "already registered" because name.com omits `purchasable`
  for rows it did not resolve, not only for taken ones.
- The generated abuse report asserted customers had been defrauded. Nobody had evidenced that.

Each is now a test named after the failure. Do not relax them.

## 2. Reads are free, writes are not

The name.com dev sandbox is not provisioned on this account, so reads run against production.
`_guard_spend` refuses `register()` and `redirect()` unless `DOPPEL_ALLOW_SPEND=1`. `confirm=true`
from the UI is deliberately not enough: a demo click must never be one keystroke from a purchase.
The deployed image does not set that variable.

## 3. Provenance travels with every value

Every finding carries whether it came from a live API or a fixture, and which query produced it.
An unreachable API says so — `availability` returns `live=False` when every lookup failed,
because the deployed console once reported `live: true` while name.com refused its IP and showed
47 unknown rows as if they were answers.

## 4. The model recommends, it never decides

`assessor.py` exists because rules cannot separate a sub-brand from an impersonator. It may not
raise a finding's band, and a verdict with no quoted evidence is discarded. Its output feeds an
abuse report a registrar will read.

## 5. Verification loops

> **A green test suite is evidence about the tests, not the product.**

- Run it. Four bugs shipped past a full green suite because no test called the endpoint.
- Read the browser console. Two features were absent from the file entirely while pytest passed.
- **A string replace that matches nothing still exits 0.** Verify the result, never the exit code.
- Check live data against reality. The Pimlico sweep looked right until the domains were
  followed and five of six turned out to be Pimlico's own.

## 6. The two stores must not diverge

`model.Store` (JSON) and `xano.XanoStore` satisfy the same nine methods; `test_store_contract`
compares their signatures. It has already caught a rename that would have made behaviour depend
on whether Xano was configured.

## 7. Style

Match the surrounding code. Comments explain *why* — the threshold's source, the bug this shape
once caused. Do not annotate the obvious.
