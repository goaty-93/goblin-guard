# Threat model

Status: design review; no implementation
Prepared: 25 August 2026

## Protected assets

- Alpaca paper credentials and paper-account state.
- OpenAI API credential and usage budget.
- Deterministic risk policy and kill-switch state.
- Decision and order idempotency records.
- Accuracy of the judge-visible audit trail.
- Separation from Profit Goblin source, data, history, and credentials.

## Trust zones

1. **Public browser:** untrusted input and visible output only.
2. **Application server:** validates requests, builds evidence, invokes the
   model, runs policy, and owns broker access.
3. **OpenAI API:** receives the minimum evidence packet and returns a structured
   proposal; it receives no Alpaca credential.
4. **Alpaca paper API:** receives only deterministic, approved order requests.
5. **Public repository:** contains source and synthetic fixtures only.

No secret crosses into browser JavaScript, public fixtures, screenshots,
presentation media, or model input.

## Principal threats and controls

| Threat | Consequence | Required control |
|---|---|---|
| Live credentials or endpoint used accidentally | Real-money exposure | Dedicated Paper Only account; explicit endpoint allowlist; fail closed |
| Prompt injection in news/evidence | Model attempts policy or tool override | Evidence treated as quoted data; strict schema; no broker tools; deterministic policy |
| Model invents facts | Misleading proposal | Evidence-ID grounding; unsupported-claim rejection; fixed evals |
| Model requests excessive size | Excessive paper exposure | Deterministic resize/reject limits; confidence has no authority |
| Duplicate request/retry | Duplicate paper order | Correlation ID plus client order ID; reconcile before retry |
| Ambiguous broker timeout | Blind resubmission | Unknown state; lookup by client order ID; block retry |
| Public user triggers repeated calls | API cost/order spam | Human confirmation, rate limit, session limit, disabled public broker action by default |
| Browser receives credentials | Credential theft | Server-side variables only; response/log scanning; no client-prefixed secrets |
| Logs expose request or account data | Privacy leakage | Structured redaction; bounded logging; demo-safe identifiers |
| Synthetic replay appears real | Misrepresentation | Persistent `SYNTHETIC REPLAY` label and fictional symbols |
| Public repo includes private history | Profit Goblin disclosure | New clean repository; exact staged-tree and history scans |
| Dependency or asset licence conflict | Ineligible submission | Licence inventory and notices before first public push |
| Kill switch UI differs from server state | False safety signal | Server-owned state returned with verdict; reject on unavailable state |
| Policy mutation via request fields | Risk bypass | Server-owned immutable policy; reject client-supplied policy overrides |

## Public-demo posture

The safest default hosted experience is synthetic replay. A real Alpaca paper
order requires a server-side capability flag plus an explicit user confirmation
in a controlled judging session. Anonymous visitors cannot place paper orders.

If the event requires an interactive order path for judges, use one of these in
order of preference:

1. Authenticated organizer/demo session with strict rate and notional limits.
2. Time-limited server-side capability enabled only during the judged demo.
3. User-supplied paper OAuth flow if feasible and explicitly required.

Do not expose a shared unrestricted paper-order endpoint.

## Stop conditions

- Any uncertainty about live versus paper mode.
- Any secret visible in client output, logs, Git, screenshots, or media.
- Any model path that can call Alpaca without deterministic approval.
- Any ambiguous broker result that cannot be reconciled.
- Any public artifact containing Profit Goblin source, history, data, or
  infrastructure detail.
- Any unresolved critical dependency licence.
