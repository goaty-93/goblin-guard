# Goblin Guard

**AI proposes. Deterministic rules decide.**

Goblin Guard is an explainable, paper-trading-only prototype for the Alpaca AI Trading Agents Hackathon. It turns validated market evidence into a schema-constrained AI proposal, then independently approves, resizes, or rejects that proposal using deterministic policy.

> **Safety status:** order submission is disabled by default. A narrowly scoped Alpaca paper-order adapter exists for tested, explicit use, but it is not connected to any HTTP endpoint or public control. This is a research and demonstration project, not financial advice or a production trading system.

## What works today

- Normalizes read-only Alpaca IEX bars into content-addressed evidence packets.
- Reads Alpaca's paper market clock through a GET-only, host-pinned client.
- Calculates EMA20, RSI14, ATR14, and a 20-bar volume ratio locally.
- Requests strict structured proposals from the OpenAI Responses API with no tools.
- Revalidates every model response against the exact evidence identifier.
- Applies deterministic paper-mode, kill-switch, market-session, universe, freshness, daily-loss, and size checks.
- Records evidence, proposal, and verdict events in an append-only, mode-`0600` JSONL audit trace.
- Provides synthetic approved/resized and rejected replays plus live read-only evaluation across a fixed six-symbol universe.
- Scans AAPL, MSFT, AMZN, GOOGL, META, and NVDA once each, shows every outcome, and deterministically nominates at most one eligible long-only candidate.
- Contains a disabled-by-default paper adapter with paper-host pinning, account/asset preflight checks, deterministic client order IDs, duplicate prevention, reconciliation, and correlated audit events.

## Verified paper execution

On 1 September 2026, the operator-only workflow scanned the fixed six-symbol universe, selected MSFT by the documented confidence rule, recomputed fresh evidence, received explicit human confirmation, and submitted one `$1.00` Alpaca paper buy. Alpaca filled `0.001976537` MSFT at an average price of `$500.876`. The public demo shows a sanitized receipt tied to commit `f06b426`; it exposes no credentials, account identifier, balance, or order control.

This proves the guarded integration and reconciliation path, not profitability, predictive value, or safe unattended autonomy.

## Trust boundary

```text
validated evidence
  -> constrained AI proposal
  -> local schema validation
  -> deterministic governor
  -> verdict and audit trace
```

The model receives neither broker credentials nor execution tools, and it cannot change policy, write audit history, authorize itself, or invoke the paper adapter. The adapter accepts only a completed approved/resized `WorkflowResult` and still requires an explicit local enable flag.

## Requirements

- Python 3.12 or newer
- Node.js 20 or newer
- npm
- Optional dedicated Alpaca paper credentials for live read-only evidence
- Optional dedicated OpenAI API key for the live proposal workflow

The synthetic workflow and test suite require no credentials.

## Clean-clone setup

```bash
git clone <repository-url> goblin-guard
cd goblin-guard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm ci
```

Start the API:

```bash
PYTHONPATH=backend .venv/bin/uvicorn goblin_guard.api:app --host 127.0.0.1 --port 8000
```

In another terminal, start the console:

```bash
npm run dev -- --host 127.0.0.1 --port 4173
```

Open [http://127.0.0.1:4173/](http://127.0.0.1:4173/). Synthetic replay works immediately.

## Optional live read-only workflow

Copy the names-only example and populate it locally with dedicated, low-scope credentials:

```bash
cp .env.example .env
chmod 600 .env
```

Load those values only into the API process:

```bash
set -a
source .env
set +a
PYTHONPATH=backend .venv/bin/uvicorn goblin_guard.api:app --host 127.0.0.1 --port 8000
```

The browser never receives these credentials. Alpaca credentials are sent in request headers, not URLs or evidence. The browser live endpoint supports only `AAPL` and `MSFT`, always treats broker paper mode as unverified, and always returns `orderSubmission: disabled`. The wider six-symbol scan is operator-only.

## Verification

Run the backend suite:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

Build the production frontend and validate its hosting wrapper:

```bash
npm run build
npm run test:sites
```

Confirm that no order route exists:

```bash
curl -i -X POST -H 'Content-Type: application/json' \
  --data '{"symbol":"AAPL"}' http://127.0.0.1:8000/api/orders
```

The expected response is HTTP `404`.

Build a credential-free evidence packet directly:

```bash
PYTHONPATH=backend .venv/bin/python -m goblin_guard.evidence_cli AAPL --synthetic
```

## Operator-only paper-order rehearsal

The paper-order command defaults to preview-only behavior and caps the governor-approved notional at `$1.00`. Rehearse the complete approval and client-order-ID flow without credentials or broker access:

```bash
PYTHONPATH=backend .venv/bin/python -m goblin_guard.paper_order_cli --synthetic
```

Prepare a live read-only proposal and verdict without submitting it:

```bash
set -a
source .env
set +a
PYTHONPATH=backend .venv/bin/python -m goblin_guard.paper_order_cli --symbol AAPL
```

Scan the fixed six-symbol universe and nominate at most one eligible candidate:

```bash
set -a
source .env
set +a
PYTHONPATH=backend .venv/bin/python -m goblin_guard.paper_scan_cli
```

The scan has no execution option and cannot submit an order. It evaluates every symbol once against one account/clock snapshot, displays failures as well as holds/rejections, and selects by highest confidence then ticker symbol. A later order still requires a fresh single-symbol run and its separate explicit confirmation.

The command will exit without submission when the market is closed or any governor check fails. Actual paper submission additionally requires `--execute` and typing the complete deterministic client order ID displayed by that same run. Synthetic mode can never be combined with `--execute`. Do not use the execution flag with live brokerage credentials.

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health and order-disabled status |
| `POST` | `/api/evaluations/synthetic` | Approved/resized or rejected replay |
| `POST` | `/api/evaluations/live` | Read-only AAPL/MSFT evidence and proposal evaluation |

No `/api/orders` route is implemented. The paper adapter is a backend library boundary, not a browser-accessible capability.

## Repository structure

- `backend/goblin_guard/` — evidence, provider, indicators, governor, audit, and API
- `backend/tests/` — boundary and regression tests
- `src/` — React guardrail console
- `planning/` — architecture, threat model, build plan, and submission notes
- `worker/` and `.openai/` — static hosting wrapper and configuration

## Security and limitations

See [SECURITY.md](SECURITY.md) for credential handling and vulnerability reporting. Third-party packages are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and locked by `package-lock.json` and `requirements.txt`.

Current limitations include a small demonstration universe, no authentication, ephemeral API audit files, no persisted decision browser, and no browser/API order control. The live workflow is designed to fail closed when credentials, evidence, clock state, or model output are unavailable or invalid. Paper submission remains disabled by default and is available only through the explicit operator CLI; one bounded paper order has been exercised and reconciled.

## Licence

Goblin Guard is available under the [MIT License](LICENSE).
