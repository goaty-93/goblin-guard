# Goblin Guard

**AI proposes. Deterministic rules decide.**

Goblin Guard is an explainable, paper-trading-only prototype for the Alpaca AI Trading Agents Hackathon. It turns validated market evidence into a schema-constrained AI proposal, then independently approves, resizes, or rejects that proposal using deterministic policy.

> **Safety status:** order submission is disabled. This repository has no broker-order adapter and no order endpoint. It is a research and demonstration project, not financial advice or a production trading system.

## What works today

- Normalizes read-only Alpaca IEX bars into content-addressed evidence packets.
- Reads Alpaca's paper market clock through a GET-only, host-pinned client.
- Calculates EMA20, RSI14, ATR14, and a 20-bar volume ratio locally.
- Requests strict structured proposals from the OpenAI Responses API with no tools.
- Revalidates every model response against the exact evidence identifier.
- Applies deterministic paper-mode, kill-switch, market-session, universe, freshness, daily-loss, and size checks.
- Records evidence, proposal, and verdict events in an append-only, mode-`0600` JSONL audit trace.
- Provides synthetic approved/resized and rejected replays plus a live read-only AAPL/MSFT evaluation.

## Trust boundary

```text
validated evidence
  -> constrained AI proposal
  -> local schema validation
  -> deterministic governor
  -> verdict and audit trace
```

There is intentionally no final order-submission step. The model receives neither broker credentials nor execution tools, and it cannot change policy, write audit history, or authorize itself.

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

The browser never receives these credentials. Alpaca credentials are sent in request headers, not URLs or evidence. The live endpoint supports only `AAPL` and `MSFT`, always treats broker paper mode as unverified, and always returns `orderSubmission: disabled`.

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

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health and order-disabled status |
| `POST` | `/api/evaluations/synthetic` | Approved/resized or rejected replay |
| `POST` | `/api/evaluations/live` | Read-only AAPL/MSFT evidence and proposal evaluation |

No `/api/orders` route is implemented.

## Repository structure

- `backend/goblin_guard/` — evidence, provider, indicators, governor, audit, and API
- `backend/tests/` — boundary and regression tests
- `src/` — React guardrail console
- `planning/` — architecture, threat model, build plan, and submission notes
- `worker/` and `.openai/` — static hosting wrapper and configuration

## Security and limitations

See [SECURITY.md](SECURITY.md) for credential handling and vulnerability reporting. Third-party packages are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and locked by `package-lock.json` and `requirements.txt`.

Current limitations include a small demonstration universe, no authentication, ephemeral API audit files, no persisted decision browser, no account/position reads, and no order submission or reconciliation. The live workflow is designed to fail closed when credentials, evidence, clock state, or model output are unavailable or invalid.

## Licence

Goblin Guard is available under the [MIT License](LICENSE).
