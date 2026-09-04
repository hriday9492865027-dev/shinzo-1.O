# Shinzo AI — Safety Policy

## Layered Design
Safety is never a single system prompt. It combines:
1. **Rules** (`app/safety/rules.py`) — deterministic checks for known critical patterns.
2. **Regex** (`app/safety/patterns.py`) — explicit pattern library, versioned and reviewed.
3. **ML classifier** (`app/safety/classifier.py`) — handles ambiguous language rules/regex miss.
4. **Risk scoring** (`app/safety/risk_scoring.py`) — combines 1-3 into LOW / MEDIUM / HIGH.
5. **Response routing** (`app/safety/response_routing.py`) — selects the behavior for that tier.

## Risk Tiers
- **LOW** — normal flow, full pipeline (§ARCHITECTURE.md) runs normally.
- **MEDIUM** — careful flow: safety-aware framing injected into context, no clinical language,
  no premature crisis response, response still conversational.
- **HIGH** — safety-oriented response path: prioritizes stabilizing, non-judgmental language and
  (in the real product) surfaces crisis resources; conversational personality features (jokes,
  teasing, proactive engine) are suppressed for that turn.

## Explicit Non-Goals
- Safety must **not** turn every expression of sadness into a crisis protocol (this destroys trust
  and product usefulness).
- Safety must **not** stay silent on genuine risk signals to preserve "natural" tone.
- Shinzo is never framed as a medical or mental-health professional at any risk tier.

## What Safety Must Never Allow Downstream
- No proactive message content generated in the same turn a HIGH risk tier fires.
- No memory write of raw high-risk content beyond what's needed for continuity of care within
  the app itself (exact data retention rules to be finalized before any real user data is stored).

## Testing
`tests/test_safety.py` and `evaluation/safety.json` are the authoritative check that routing
behaves as specified above; both must pass before Milestone 15 (full orchestrator) is considered done.
