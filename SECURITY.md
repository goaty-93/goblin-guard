# Security policy

## Prototype scope

Goblin Guard is a paper-trading-only hackathon prototype. Order submission is disabled, and the repository intentionally contains no broker-order adapter or order endpoint.

## Credential handling

- Use dedicated, low-scope Alpaca paper credentials and a dedicated OpenAI project key.
- Store credentials only in the ignored `.env` file with mode `0600` or in the deployment platform's secret store.
- Never put credentials in browser code, URLs, evidence packets, fixtures, screenshots, issues, or commits.
- Rotate a credential immediately if it may have been exposed.

The live API keeps credentials server-side. Alpaca requests use authentication headers, and the OpenAI request exposes no broker tools or credentials.

## Reporting a vulnerability

Do not open a public issue containing sensitive details or credentials. Contact the repository owner privately with a minimal reproduction, affected revision, and impact. This prototype does not currently promise a formal response SLA.

## Unsupported use

Do not use this project with live brokerage credentials, real-money accounts, or as a production trading or investment system.
