# Goblin Guard

Goblin Guard is an explainable, paper-trading-only agent for the Alpaca AI Trading Agents Hackathon. AI may propose a trade; deterministic code independently validates evidence and approves, resizes, or rejects the proposal.

The Day 1 demo is a synthetic replay. It has no broker credentials and cannot submit orders.

## Run the console

```bash
npm install
npm run dev
```

## Run the deterministic governor tests

```bash
PYTHONPATH=backend python3 -m unittest discover -s backend/tests -v
```

## Safety boundary

`evidence -> AI proposal -> schema validation -> deterministic risk governor -> paper-order adapter -> audit trace`

The model never receives broker order tools or broker credentials. The future paper-order adapter remains disconnected until its endpoint, idempotency, reconciliation, and kill-switch gates are tested.
