# Public-release boundary

## Default decision

Create a new repository during the official build window. Do not fork, mirror,
make public, or rewrite the history of the private Profit Goblin repository.
No publication occurs without explicit approval after reviewing the exact
candidate tree.

## Safe conceptual reuse

The following concepts may inform a clean implementation, subject to the final
event rules and an authorship/licensing review:

- Deterministic proposal validation.
- Long-only position sizing.
- Maximum position and portfolio exposure.
- Maximum open-position count.
- Drawdown and daily-loss circuit breakers.
- Exit-before-entry processing.
- Explicit rejection reasons.
- Append-only decision and order audit records.
- Alpaca market-data adapter patterns documented by Alpaca.
- A small, synthetic replay fixture created specifically for the entry.

Conceptual reuse does not automatically authorize copying private source.

## Candidate areas for narrow, line-by-line review

These files identify useful ideas but are not pre-approved for copying:

- `backend/app/risk.py`
- `backend/app/market_data.py`
- `backend/app/indicators.py`
- `backend/app/goblin_wire/alpaca_news_provider.py`
- `backend/app/goblin_wire/intraday_provider.py`
- Selected tests that describe generic safety invariants

Any approved extraction should be the smallest coherent unit, stripped of
private strategy parameters and accompanied by provenance notes.

## Never publish

- `.env`, API keys, secrets, tokens, account identifiers, or logs containing
  them.
- SQLite databases, WAL/SHM files, exports, backups, screenshots of private
  portfolios, or production observations.
- NAS paths, addresses, deployment scripts, Compose production configuration,
  private DNS names, scheduler state, or operational history.
- Profit Goblin's `.git` directory, commit history, branches, tags, or remotes.
- Proprietary strategy research, parameter sweeps, private watchlists, thesis
  records, Lantern history, or Goblin Wire research history.
- Private fixtures, personal data, generated production artefacts, or copied
  third-party content.
- The private frontend wholesale; the hackathon UI should be a small new
  implementation.
- Any code or asset whose licence or authorship cannot be established.

## Dependency review gate

The current private application uses FastAPI, Uvicorn, SQLAlchemy, Pydantic,
Pandas, NumPy, alpaca-py, HTTPX, pytest, yfinance, lxml, React, Vite,
react-icons, and Recharts. Their names in the current manifests are inventory,
not licence clearance.

Before the public repository is published:

- Generate a dependency list with exact versions and licences.
- Confirm every runtime and bundled asset licence is compatible with the
  chosen repository licence.
- Retain required copyright and licence notices.
- Remove unused dependencies.
- Do not bundle market/news data unless its redistribution terms permit it.
- Use synthetic fixtures for the public demo and tests wherever possible.

## Secret and history gates

Before first push and before every submission update:

- Inspect the complete staged tree, not just the visible diff.
- Scan tracked files and Git history for credentials and private identifiers.
- Confirm `.env*`, databases, logs, exports, coverage, build outputs, and local
  caches are ignored.
- Confirm the public remote is the intended repository.
- Confirm the repository licence matches the organizer's answer.
- Confirm the demo uses environment variables and paper-only Alpaca endpoints.
