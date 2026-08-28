# Technical decisions

Status: pre-kickoff design decision; no implementation
Checked: 24 August 2026

## Decision summary

| Area | Primary choice | Fallback | Reason |
|---|---|---|---|
| AI API | OpenAI Responses API | Synthetic proposal fixture | Structured, bounded proposal generation rather than free-form execution |
| AI model | `gpt-5.6-luna`, low reasoning | `gpt-5.6-terra`, low reasoning | Luna is the cost-sensitive GPT-5.6 tier and supports structured outputs; compare Terra only if representative evaluations show a material quality gain |
| Alpaca | Direct Trading and Market Data APIs | Synthetic replay | Keeps credentials and execution inside deterministic application code |
| Order mode | Alpaca paper-only account and paper endpoint | No order submission | Live mode is never a fallback |
| Alpaca MCP/CLI | Not in the initial build | Add one only if event rules require it | Avoid giving the model a broker-order tool; preserve the product's trust boundary |
| Backend | Small FastAPI service | Static replay-only demo | Matches the intended typed validation and broker adapter |
| Frontend | Focused React/Vite dashboard | Single static decision trace | Supports the selected Guardrail Console design without rebuilding Profit Goblin |
| Hosting | Vercel | Organizer-approved alternative | LabLab names Vercel, and Vercel documents FastAPI/Python support and environment variables |
| Persistence | Session-scoped audit record plus committed synthetic fixtures | Browser-local replay | Avoid a database dependency for the judging path |

These choices remain private and provisional until the kickoff rules and
organizer answers are recorded.

## AI contract

The AI receives only a compact, immutable evidence packet. It returns exactly
one proposal matching `goblin_guard_proposal_v1` through strict structured
output. It has no Alpaca credential, order tool, risk-limit mutation tool,
shell, network tool, or direct persistence access.

Start with `gpt-5.6-luna` and low reasoning because the task is bounded: select
`buy`, `sell`, or `hold`; cite supplied evidence IDs; propose a notional; and
write a concise rationale. Model confidence is descriptive and cannot loosen a
gate.

Before submission, run the same representative fixtures through Luna and
Terra. Promote Terra only if it materially improves schema validity, evidence
grounding, action consistency, or judge-facing rationale enough to justify its
higher cost/latency. Do not select a model from one attractive example.

Required evaluation dimensions:

- Valid schema on the first response.
- Every claim traceable to a supplied evidence reference.
- No invented price, timestamp, position, account, or news fact.
- Stable action on semantically identical evidence.
- Correct `hold` response when required evidence is missing.
- Bounded rationale with no hidden chain-of-thought request or display.
- No attempt to override, reinterpret, or call the deterministic governor.

## Alpaca contract

Use a dedicated Paper Only account where practical. Paper trading uses separate
credentials and the `https://paper-api.alpaca.markets` trading endpoint. The
application must verify the configured endpoint and account state before every
submission and fail closed if mode is ambiguous.

Broker responsibilities remain deterministic:

- Read account, asset, position, and open-order state.
- Normalize approved notional to a supported order request.
- Assign a deterministic, unique `client_order_id`.
- Persist the Alpaca request ID when available.
- On timeout or ambiguous response, query by `client_order_id` before retrying.
- Reject duplicate correlated submissions.
- Render paper status and broker outcome without exposing account identifiers.

The direct Trading API is the initial integration because it makes the
authority boundary explicit. Alpaca MCP exposes trading tools and Alpaca CLI
supports order commands, but neither belongs inside the proposal agent by
default. If the event requires MCP or CLI, use it in a separately scoped,
read-only evidence adapter or behind the deterministic governor; never expose
an unrestricted order tool to the model.

## Hosting contract

Use one Vercel project containing the focused frontend and a small FastAPI
backend. Store API credentials only as server-side sensitive environment
variables. Never expose them through client-prefixed variables, build output,
logs, responses, or screenshots.

The public judging path must not depend on durable server filesystem state.
Each evaluation returns a complete audit trace to the browser. The synthetic
replays are versioned, immutable fixtures in the public repository and require
no external API. A real paper-order demonstration may use transient server-side
state plus Alpaca reconciliation, but the order remains identifiable by its
client order ID.

Hosting gates:

- Fresh signed-out browser can open the demo.
- Synthetic approved and rejected replays work without credentials.
- Live API controls are disabled when server-side credentials are absent.
- No secret reaches browser JavaScript or static assets.
- Cold start and model timeout return a readable fail-closed state.
- Public demo revision is tied to the submitted Git SHA.

## Account and cost preparation

Before kickoff, verify only account readiness; do not build the entry:

- A distinct Alpaca paper credential pair can be created and rotated.
- The account is visibly paper-only and has IEX access sufficient for the demo.
- An OpenAI API project has an explicit small usage budget and no unrelated
  credentials.
- A Vercel account can create a private preview project before publication if
  the organizer permits it.
- All credentials are held outside Git and can be revoked after judging.

Do not place credentials or account output into planning documents or chat.

## Open questions

- Does the event require Alpaca MCP or CLI, or is the Trading API sufficient?
- Is an OpenAI model acceptable, or is a sponsor-provided model expected?
- Does the organizer require durable audit history in the hosted demo?
- Are scheduled autonomous runs expected, or is human-triggered agency enough?
