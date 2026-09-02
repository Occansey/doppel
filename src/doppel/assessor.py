"""The judgement the rules deliberately refuse to make.

triage.py caps a search-discovered host below "live scam" because a legitimate sub-brand and
an impersonator are string-identical -- pimlicoplumbersfranchise.co.uk is Pimlico's own site,
and a rule that reads names cannot know that. Something has to actually look at the page.

That is what this does. It fetches both sites, hands the model what it saw, and asks one
question: is this the same organisation, a different one trading honestly, or someone dressed
as the business?

Two constraints, both enforced rather than hoped for:
  - It never raises a finding's band on its own. It produces a recommendation for a human.
    A model that could escalate to "live scam" would reintroduce exactly the false accusation
    the rules were changed to prevent.
  - It must cite what it saw. A verdict with no quoted evidence is discarded, because the
    output of this feeds an abuse report that a registrar will read.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import httpx

MODEL = "gemini-3.6-flash"
FALLBACK = "gemini-2.5-flash"

VERDICTS = ("same_organisation", "unrelated_business", "dressed_as_you", "cannot_tell")


@dataclass(frozen=True)
class Assessment:
    verdict: str
    confidence: str          # low | medium | high
    reasoning: str
    evidence: list[str]      # quoted from the pages; empty means the verdict is discarded
    model: str
    usable: bool


def _text(url: str, limit: int = 6000) -> str:
    try:
        with httpx.Client(timeout=12, follow_redirects=True,
                          headers={"user-agent": "Mozilla/5.0 (Doppel)"}) as c:
            html = c.get(url).text
    except Exception as e:
        return f"[unreachable: {e.__class__.__name__}]"
    html = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html)
    title = (re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1]
    body = re.sub(r"<[^>]+>", " ", html)
    return f"TITLE: {title.strip()}\n\n{' '.join(body.split())[:limit]}"


PROMPT = """You are helping a small business work out whether another website is impersonating it.

THE REAL BUSINESS — {real_domain}
{real_text}

THE DOMAIN IN QUESTION — {suspect_domain}
{suspect_text}

Decide which of these it is:
  same_organisation   a site belonging to the same company (franchise, careers, shop, regional)
  unrelated_business  a genuine different business that happens to share words
  dressed_as_you      presenting itself as the business in order to take its customers
  cannot_tell         not enough evidence

Rules:
- Quote short phrases you actually saw. Do not invent.
- A shared trade word ("plumbers", "roofing") is not impersonation.
- Copied branding, matching contact details, or a payment flow using the other's name is.
- If the suspect page was unreachable, answer cannot_tell.

Reply with JSON only:
{{"verdict": "...", "confidence": "low|medium|high", "reasoning": "one or two sentences",
  "evidence": ["short quote", "short quote"]}}"""


def assess(suspect_domain: str, real_domain: str, *, _client=None) -> Assessment:
    client = _client
    if client is None:
        try:
            from google import genai
            client = genai.Client(vertexai=True, location="global",
                                  project=os.getenv("GOOGLE_CLOUD_PROJECT",
                                                    "nightshift-agentic-2026"))
        except Exception as e:
            return Assessment("cannot_tell", "low", f"model unavailable: {e}", [], "none", False)

    prompt = PROMPT.format(real_domain=real_domain, suspect_domain=suspect_domain,
                           real_text=_text(f"https://{real_domain}"),
                           suspect_text=_text(f"http://{suspect_domain}"))
    for model in (MODEL, FALLBACK):
        try:
            raw = (client.models.generate_content(model=model, contents=prompt).text or "").strip()
        except Exception:
            continue
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
        try:
            d = json.loads(raw)
        except Exception:
            continue
        verdict = d.get("verdict") if d.get("verdict") in VERDICTS else "cannot_tell"
        evidence = [str(x)[:200] for x in (d.get("evidence") or [])][:4]
        return Assessment(
            verdict=verdict,
            confidence=d.get("confidence", "low"),
            reasoning=str(d.get("reasoning", ""))[:400],
            evidence=evidence,
            model=model,
            # No evidence, no verdict. This feeds an abuse report a registrar will read.
            usable=bool(evidence) and verdict != "cannot_tell",
        )
    return Assessment("cannot_tell", "low", "no model answered", [], "none", False)


def recommendation(a: Assessment) -> str:
    """What the human is being asked to decide. Never an action taken automatically."""
    if not a.usable:
        return "No usable assessment — decide this one yourself."
    return {
        "same_organisation": "Looks like your own site. Mark it 'harmless' unless you disagree.",
        "unrelated_business": "A different business sharing words with you. Probably harmless.",
        "dressed_as_you": "Reads as impersonation. Review the evidence, then mark it 'hostile' "
                          "to build the abuse report.",
    }.get(a.verdict, "Decide this one yourself.")
