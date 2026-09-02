---
name: sweep
description: Run a live Doppel sweep against a business and read the result honestly. Use when checking whether the pipeline works end to end, or before recording a demo.
---

# Running a live sweep

```bash
cd 01-devnetwork-api-cloud-ai && set -a && . ./.env && set +a
PYTHONPATH=src ./.venv/bin/python - <<'PY'
from doppel.variants import generate
from doppel import adapters, destination as dest, triage
BIZ, DOM, ANCH = "Pimlico Plumbers", "pimlicoplumbers.com", ["London"]
vs = generate(DOM, limit=40)
av = adapters.availability([v.domain for v in vs])
print("availability live:", av.live, "|", av.source)
for v in vs:
    if av.value[v.domain]["registered"]:
        d = dest.classify(v.domain, DOM)
        s = triage.score(technique=v.technique, registered=True, destination=d.verdict)
        print(f"{s:>3} {triage.band(s):<16} {v.domain:<32} -> {d.verdict}")
PY
```

## Reading the result

- **`availability live: False`** means name.com refused this host. The API allowlists by IP.
  Cloud Run is not on the list; this machine is. Do not present those rows as answers.
- **`already yours`** is the common case for a healthy business. Five of six registered Pimlico
  lookalikes redirect to the real site. A sweep that alarms on all of them is broken.
- **A plausible-looking count of registered domains is the thing to distrust.** 28 of 60 was
  wrong; 1 of 60 was right.

## Before recording a demo

Reset the tables, run one sweep, then a second so the change monitor has something to diff.
Confirm the ticker reads `serpapi LIVE · name.com LIVE · store XanoStore`.
