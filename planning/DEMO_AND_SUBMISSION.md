# Demo and submission plan

## One-sentence pitch

Goblin Guard lets an AI trading agent make a case, but only deterministic,
auditable controls can authorize an Alpaca paper order.

## Target user

A technically capable retail systematic trader or small research team that
wants agent-assisted decision-making without giving an LLM unrestricted broker
authority.

## Primary demo story

The judge should understand the product in the first 30 seconds.

1. Open on a three-column decision trace: evidence, AI proposal, risk verdict.
2. Run a proposal whose evidence is fresh and whose requested size is too large.
3. Show the governor resize it to the permitted notional and explain every gate.
4. Submit the resized order to an Alpaca paper account.
5. Show the broker response and correlated audit record.
6. Run a second proposal while a daily-loss or stale-evidence gate is active.
7. Show a deterministic rejection even though the AI recommends buying.
8. End on paper-account state, kill switch, and replayable decision history.

The winning moment is the contrast: the AI can be persuasive and still be
overruled by policy. The public demo now opens on a sanitized, verified run:
six symbols scanned once each, MSFT selected by a fixed ranking rule, a fresh
human-authorized `$1.00` paper buy, and the reconciled broker fill. The original
approved/resized and rejected cases remain available under Decision cases.

## Demo reliability

- Rehearse with the market open and closed.
- Use deterministic client order IDs and safe cleanup/reconciliation.
- Use the sanitized verified MSFT fill as the pre-recorded broker-response path.
- Provide a clearly labelled synthetic replay that needs no external API.
- Never display API keys, account identifiers, private balances, browser
  autofill, or unrelated tabs.
- Keep the hosted public demo on a separate paper account with minimal scope.
- Add a visible timestamp and `PAPER TRADING ONLY` label to every decision.

## Five-minute video storyboard

- **0:00–0:25:** Problem — LLM trading agents can be opaque and over-authorized.
- **0:25–0:50:** Product — AI proposes; deterministic governance disposes.
- **0:50–2:35:** Live approved/resized proposal and Alpaca paper order.
- **2:35–3:25:** Rejected proposal and kill-switch demonstration.
- **3:25–4:05:** Architecture, auditability, and failure handling.
- **4:05–4:35:** Target user and business model.
- **4:35–5:00:** Differentiation, roadmap, paper-only disclaimer, team.

## Slide skeleton

1. Goblin Guard: trustworthy autonomy for paper trading.
2. Problem: reasoning systems should not be their own risk authority.
3. Product: evidence to proposal to deterministic gates to Alpaca.
4. Demo results: approved/resized and rejected traces.
5. Architecture and safety boundary.
6. Target user, business value, and plausible SaaS/research-tool model.
7. Differentiation and roadmap.
8. Team, technology, repository, demo URL, and disclaimer.

Do not invent market-size figures. Any TAM/SAM claim needs a cited, current
source and transparent method.

## Submission copy scaffolding

### Title

Goblin Guard

### Short description draft

An explainable Alpaca paper-trading agent where AI proposes trades and
deterministic risk controls approve, resize, or reject every action.

### Long-description outline

- The control problem with autonomous trading agents.
- The target user and concrete workflow.
- Alpaca data and paper-order integration.
- Structured AI proposals rather than free-form execution.
- Independent deterministic risk and reconciliation controls.
- Judge-visible audit history and synthetic replay.
- Paper-only safety posture and future potential.

## Evidence checklist

- Public repository and clean clone instructions tested.
- Licence and dependency notices present.
- No secrets or private history in the repository.
- Hosted URL works in a signed-out/private browser session.
- Health endpoint and visible paper-only status pass.
- At least one approved/resized trace recorded.
- At least one rejected trace recorded.
- Alpaca paper order and reconciliation demonstrated: MSFT `$1.00`, filled on
  1 September 2026, with the public receipt sanitized.
- Kill switch demonstrated.
- Synthetic fallback replay works without external APIs.
- Video is MP4, at most five minutes, and contains no sensitive information.
- Deck is PDF and readable at presentation size.
- Cover is PNG/JPG and 16:9.
- Title, descriptions, tags, repository, URL, video, and deck are populated.
- Final submission is completed before the normal deadline, not the manual
  exception window.
