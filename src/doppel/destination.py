"""Where does a registered lookalike actually go?

Availability tells you somebody owns it. It does not tell you *who*, and the distinction is
the whole difference between an alarm and a non-event: most registered lookalikes of a healthy
business are owned by that business, parked and redirecting to the real site.

Checked against Pimlico Plumbers, five of six registered lookalikes redirected to the real
domain. A tool that called those six impersonations would be wrong five times out of six --
and a business that is cried wolf at once stops opening the emails.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class Destination:
    reachable: bool
    final_host: str | None
    verdict: str          # "ours" | "elsewhere" | "parked" | "unreachable"
    detail: str


def _host(url: str) -> str:
    return url.split("//")[-1].split("/")[0].removeprefix("www.").lower()


def classify(domain: str, real_domain: str, *, client: httpx.Client | None = None) -> Destination:
    """Follow the domain and see where it lands. Read-only, and deliberately short-timeout:
    a squatter's parking page is often slow, and a sweep must not hang on it."""
    real = real_domain.removeprefix("www.").lower()
    own = client or httpx.Client(timeout=8, follow_redirects=True,
                                 headers={"user-agent": "Mozilla/5.0 (Doppel)"})
    try:
        r = own.get(f"http://{domain}")
        final = _host(str(r.url))
        if final == real:
            return Destination(True, final, "ours",
                               "Redirects to your own site — this is already yours, or someone "
                               "is pointing traffic back to you. No action needed.")
        if final == domain.removeprefix("www.").lower():
            return Destination(True, final, "parked",
                               "Resolves but stays on its own name. Could be a parking page "
                               "or a copy of your site. Worth looking at.")
        return Destination(True, final, "elsewhere",
                           f"Sends visitors to {final}, which is neither you nor itself.")
    except Exception:
        return Destination(False, None, "unreachable",
                           "Registered but nothing answers. Held, not yet used.")
    finally:
        if client is None:
            own.close()
