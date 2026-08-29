# Design QA

Reference: `design/guardrail-console-selected.png`

Viewport: 1487 × 1058

## Visual comparison

- Header anatomy, console split, proposal density, guardrail stack, oversized verdict, trace table, and replay call-to-action match the selected direction.
- The generated shield asset is used as a real raster asset with its white background removed; no placeholder or CSS-drawn branding remains.
- The implementation deliberately labels the Day 1 experience as a synthetic replay and uses requested notional rather than live share quantity because no broker connection exists yet.
- Responsive rules collapse the split console to one column below 1000px and simplify trace metadata below 680px.

## Interaction and runtime checks

- Replay switches between a rejected stale/daily-loss case and an approved-with-resize case.
- Replay now executes those cases through the local FastAPI evidence → proposal → governor → audit workflow; the bundled fixtures remain the explicit offline fallback.
- Browser verification covered both API-backed verdicts and confirmed that the footer stayed `NO ORDERS` with no console warnings or errors.
- The separate live read-only control was verified with genuine Alpaca IEX evidence and an OpenAI proposal. It rendered `LIVE READ-ONLY`, failed closed on paper-mode verification and stale completed-session data, and kept `NO ORDERS` visible.
- The primary control is keyboard-accessible and exposes a loading state.
- Browser console: no application errors observed.
- Production build and hosting-contract tests pass.

## Fixes made during QA

- Removed unintended solid backgrounds from decision-trace result text.
- Added a specific document title, theme colour, and description.

final result: passed
# Market-session and indicator milestone — 29 August 2026

- Verified the live read-only AAPL path in the rendered console at `http://127.0.0.1:4173/`.
- Alpaca's paper clock reported the US equities session closed; the deterministic `Market Session` guardrail failed closed.
- EMA20, RSI14, ATR14, and 20-bar volume ratio rendered from locally calculated, validated Alpaca IEX bars rather than placeholders.
- The structured proposal selected `HOLD`; the verdict remained `REJECTED`, with `No order submitted` and the footer `LIVE READ-ONLY · LIVE READ-ONLY WORKFLOW · NO ORDERS`.
- Browser console contained no warnings or errors.
