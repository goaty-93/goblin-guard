# Goblin Guard

Goblin Guard is an explainable, paper-trading-only agent for the Alpaca AI Trading Agents Hackathon. AI may propose a trade; deterministic code independently validates evidence and approves, resizes, or rejects the proposal.

The Day 1 demo is a synthetic replay. It has no broker credentials and cannot submit orders.

## Run the console

```bash
npm install
npm run dev
```

In a second terminal, run the local orderless API:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=backend .venv/bin/uvicorn goblin_guard.api:app --host 127.0.0.1 --port 8000
```

## Run the deterministic governor tests

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
```

## Build an evidence packet

The committed fixture exercises the same validation and normalization path without credentials:

```bash
PYTHONPATH=backend python3 -m goblin_guard.evidence_cli AAPL --synthetic
```

For live, read-only Alpaca IEX bars, place dedicated paper-account values in an ignored `.env`, export them into your shell, then omit `--synthetic`. Credentials are sent only as request headers and are never included in evidence, logs, URLs, or browser code.

## Proposal and audit boundary

The optional OpenAI provider uses the Responses API with strict JSON Schema output, `store: false`, and an empty tool list. Every returned proposal is validated again locally against the exact evidence ID before the deterministic governor sees it. The orderless workflow appends evidence, proposal, and verdict events to a mode-`0600` JSONL audit log under one stable correlation ID.

The current repository deliberately contains no paper-order adapter implementation.

## Safety boundary

`evidence -> AI proposal -> schema validation -> deterministic risk governor -> paper-order adapter -> audit trace`

The model never receives broker order tools or broker credentials. The future paper-order adapter remains disconnected until its endpoint, idempotency, reconciliation, and kill-switch gates are tested.
