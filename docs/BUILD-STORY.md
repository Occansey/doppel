# Build story

Required by the Xano challenge. Written honestly, including the parts that went wrong.

## What software did we replace?

**Enterprise brand protection** — MarkMonitor, ZeroFox, Red Points and the rest. They solve
domain impersonation properly and they sell it to organisations with a legal department, from
roughly $10,000 a year.

The business that actually gets impersonated is a plumber with four employees and a van. He
cannot buy that, so he buys nothing, and finds out he has been impersonated when a customer
shouts at him about a deposit he never received.

## Why that one?

Because the gap is not technical, it is commercial. Every capability here is a public API call.
What does not exist is a version priced and shaped for someone who has ten minutes and no
lawyer — which changes the product, not just the price:

- It must produce **three things to do**, not a 147-row report.
- It must **refuse to cry wolf**. A false alarm costs a small business more than a missed
  domain, because the response to an alarm is hours it does not have.
- It must hand over something a registrar will act on, because there is no legal team to
  translate findings into a complaint.

## Which AI tools?

**Claude Code**, throughout — specification, implementation, tests, and the console.

The useful pattern was not "generate code". It was writing the contract first
(`SPECIFICATION.md`, then `docs/XANO.md`), then holding the implementation against it. Three
bugs were caught that way rather than in the demo:

1. Free eye-fooling variants scored 30 and sorted into `ignore`, contradicting the ranking
   module's own docstring. Registering a free homoglyph is the cheapest win in the product.
2. Every host ranking for the brand scored 100 "live scam" — including Checkatrade. That would
   have sent a business to file an abuse report against its own review site, on camera.
3. Findings deduplicated on `url` globally instead of `(case_id, url)`, so a second case for
   the same business returned nothing. The local store had silently drifted from the unique
   index documented for Xano.

A fourth was caught in prose rather than code: the generated abuse report asserted that
customers *"believe they have paid us when they have not"* — a sentence nobody had evidenced,
placed in the business owner's mouth, in a document ending "nothing is asserted that is not in
the record". Harm is now derived from observations only.

Each of those is now a test named after the failure.

## How long?

Roughly one working day, including a full pivot. The project began as a different idea
(a digital-estate tool) and was rebuilt around impersonation once it became clear the earlier
concept failed the "would anyone actually buy this" test.

The pivot cost about twenty minutes of code, because the store contract, the Xano adapter and
the append-only ledger were written against a documented schema rather than around one
concrete use case.

## What would have taken significantly longer without AI + Xano?

**Without Xano:** the case file is the product's spine — cases, findings, human triage
decisions, and an append-only evidence ledger that has to hold up if it reaches a registrar.
Building that as auth + schema + migrations + endpoints is most of a day on its own. Defining
it as tables and function stacks moved that to under an hour, and the API surface came out
the same shape as the contract instead of drifting from it.

**Without AI:** the parts that are tedious rather than hard — the QWERTY adjacency map, the
homoglyph table, the bulk-availability batching, six variants of the scoring test. Those are
an afternoon of typing and a good place to make quiet mistakes.

**What AI did not do:** decide what to build. The first idea was wrong and no amount of code
generation would have surfaced that. It took someone saying "idea sucks".
