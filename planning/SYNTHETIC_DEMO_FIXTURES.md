# Synthetic demo fixtures

Status: specification only; values are fictional and must be clearly labelled

The demo uses two deterministic fixtures. They exist to prove behaviour when
markets, Alpaca, the model, or hosting are unavailable. They are not historical
market claims and must never be presented as real performance.

## Shared fixture contract

Each fixture contains:

- Fixture ID and schema version.
- `synthetic: true` and a visible `SYNTHETIC REPLAY` label.
- Fixed evaluation timestamp in UTC.
- Fictional evidence records with stable IDs.
- Fictional paper-account state.
- Expected AI proposal shape.
- Expected gate results in stable order.
- Expected final decision and order behaviour.
- No real news copy, customer data, account identifier, or imported market
  dataset.

## Fixture A: oversized proposal is resized and approved

Purpose: demonstrate useful AI reasoning without allowing it to choose risk.

### Evidence

- Symbol: `DEMOA` (fictional; adapter marks it as demo-only).
- Evaluation time: `2026-08-28T14:35:00Z`.
- Evidence `price-001`: reference price `$100.00`, captured 30 seconds ago.
- Evidence `trend-001`: price above fictional 20-day and 50-day averages.
- Evidence `volume-001`: fictional relative volume `1.4`.
- Evidence `news-001`: synthetic neutral-positive catalyst summary.
- Paper cash: `$10,000`.
- Existing position: zero.
- Daily realized result: `$0`.

### Expected proposal

- Action: `buy`.
- Requested notional: `$2,500`.
- Confidence: `0.72`.
- Evidence references include only the four supplied IDs.
- Concise thesis and one explicit invalidation condition.

### Policy

- Maximum order notional: `$250`.
- Maximum symbol exposure: `$500`.
- Maximum open positions: `5`.
- Daily loss breaker: not active.
- Evidence freshness maximum: 60 minutes.

### Expected verdict

- Schema, paper mode, kill switch, symbol, freshness, session, duplication,
  cash, position-count, daily-order, and loss gates: `pass`.
- Per-trade notional gate: `resize` from `$2,500` to `$250`.
- Final decision: `approved_with_resize`.
- Synthetic mode: render a fictional paper-order receipt but make no network
  call.
- Live demo mode: submit only the deterministic `$250` approved result to the
  dedicated Alpaca paper account after explicit user action.

## Fixture B: persuasive proposal is rejected

Purpose: make the core differentiation emotionally obvious: a convincing AI
recommendation cannot bypass policy.

### Evidence

- Symbol: `DEMOB` (fictional; adapter marks it as demo-only).
- Evaluation time: `2026-08-28T15:40:00Z`.
- Evidence `price-101`: reference price `$50.00`, captured 65 minutes ago.
- Evidence `trend-101`: fictional positive momentum.
- Evidence `volume-101`: fictional relative volume `1.3`.
- Paper cash: `$8,500`.
- Daily realized result: `-$172` on a `$10,000` start-of-day equity fixture.

### Expected proposal

- Action: `buy`.
- Requested notional: `$500`.
- Confidence: `0.81`.
- Rationale is plausible and cites only supplied evidence.

### Policy

- Evidence freshness maximum: 60 minutes.
- Daily loss limit: `-1.5%`.
- Global kill switch: off.

### Expected verdict

- Schema, paper mode, kill switch, symbol, exposure, and volatility gates:
  `pass` where safe to evaluate.
- Freshness gate: `reject` because evidence age is 65 minutes.
- Daily loss gate: `reject` because the fixture is below `-1.5%`.
- Final decision: `rejected`.
- No order request is constructed or submitted.
- Primary recovery action: `Replay with fresh evidence`; this does not bypass
  the daily-loss breaker, so the second evaluation remains rejected until the
  policy fixture is reset explicitly.

## Additional failure fixtures for automated tests

These do not need separate judge-facing screens:

- Invalid model JSON.
- Missing evidence reference.
- Unsupported symbol.
- Paper endpoint mismatch.
- Global kill switch active.
- Duplicate correlation/client order ID.
- Alpaca timeout followed by successful reconciliation.
- Alpaca timeout with unknown state and no retry.
- Missing OpenAI credential selects synthetic replay rather than a fake live
  result.

## Acceptance test

With networking disabled, a fresh clone can replay both primary fixtures and
produce byte-for-byte stable policy outcomes. UI wording may evolve, but gate
reason codes, final decisions, and no-order behaviour must remain deterministic.
