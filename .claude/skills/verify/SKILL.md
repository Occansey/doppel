---
name: verify
description: Check that a change actually works before claiming it does. Use after any edit to the console, an adapter, or the store.
---

# Verifying a change in Doppel

A green suite is evidence about the tests. Four bugs shipped past one because no test called
the endpoint, and two console features were absent from the file entirely while pytest passed.

## The order that catches things

1. **`pytest tests/ -q`** — fast, but it only proves what it asserts.
2. **Did the edit apply?** A `str.replace` that matches nothing still exits 0. Grep for the new
   text, or print the function list, before believing a success message.
3. **Restart the server.** `preview_start` reuses a running process; it will happily serve the
   code from before your fix and send you hunting a data bug.
4. **Read the browser console** — `read_console_messages(onlyErrors=true)`. A JS error in
   `boot()` empties the page and looks exactly like an empty dataset.
5. **Call the endpoint in-process** for a real traceback:
   `from doppel.app import changes, store; changes(cid)` — a `NameError` for a missing import
   shows up here and nowhere else.
6. **Check the numbers against reality.** Follow a domain in a browser. Read what the page says.

## Things that have lied here before

| symptom | cause |
|---|---|
| empty console, no error | `boot()` threw on a removed element |
| "run a second sweep" forever | ledger stored `Verb.SWEEP`, filter matched `sweep` |
| every report 404s | endpoint read `store._db`, absent on XanoStore |
| `live: true`, all rows unknown | API 403'd; adapter reported creds present, not calls succeeded |
| 28 of 60 "registered" | absent `purchasable` read as taken rather than unresolved |
