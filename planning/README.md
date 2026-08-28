# Goblin Guard pre-hackathon readiness pack

Status: private planning only
Prepared: 24 August 2026
Event: Alpaca AI Trading Agents Hackathon, 28 August–4 September 2026

This pack prepares a clean, bounded hackathon entry without changing Profit
Goblin's production or simulation-only behaviour. It is not the hackathon
application and contains no AI decision engine, Alpaca order client, public
repository, deployment, credentials, or production changes.

## Working concept

**Goblin Guard is an explainable Alpaca paper-trading agent where AI proposes
trades and deterministic controls independently approve, resize, or reject
every action.**

The intended differentiator is not an unconstrained trading chatbot. It is a
visible separation between probabilistic research/reasoning and deterministic
execution authority, with an auditable record of both.

## Documents

- [Rules ledger](RULES_LEDGER.md): confirmed requirements, unresolved points,
  and the questions that must be answered at kickoff.
- [Public-release boundary](PUBLIC_RELEASE_BOUNDARY.md): what may be recreated
  or extracted and what must never enter the public repository.
- [Architecture contract](ARCHITECTURE.md): planned components, trust boundary,
  proposal schema, risk gates, and failure behaviour.
- [Demo and submission](DEMO_AND_SUBMISSION.md): the primary demo story,
  fallback mode, pitch structure, and evidence checklist.
- [Seven-day build plan](BUILD_PLAN.md): daily gates, scope-cut order, and final
  submission checklist.
- [Technical decisions](TECHNICAL_DECISIONS.md): provisional AI, Alpaca,
  hosting, persistence, cost, and fallback choices.
- [Synthetic demo fixtures](SYNTHETIC_DEMO_FIXTURES.md): the deterministic
  approved/resized and rejected replay specifications.
- [Evaluation plan](EVALUATION_PLAN.md): proposal, governor, broker, UX, model
  comparison, and release acceptance gates.
- [Threat model](THREAT_MODEL.md): trust zones, principal threats, controls,
  public-demo posture, and stop conditions.
- [Kickoff checklist](KICKOFF_CHECKLIST.md): the exact rule capture, account,
  public-boundary, and start-authorization sequence for 28 August.

## Start gate for 28 August

Do not begin the competition implementation until all of these are true:

- The kickoff has occurred and its event-specific guidance has been captured.
- The organizer has clarified pre-existing code and licensing expectations.
- A new public repository boundary has been explicitly approved.
- The repository contains no Profit Goblin Git history, secrets, production
  data, private fixtures, exports, or infrastructure details.
- Paper trading remains the only broker execution mode.

## Non-goals

- Modifying, deploying, or relicensing the private Profit Goblin repository.
- Connecting Profit Goblin production to a broker order path.
- Live-money trading, options, crypto, shorting, margin, or autonomous capital
  withdrawal.
- Publishing strategy research or historical results that have not been
  explicitly approved for release.
- Claiming profitability or presenting the prototype as financial advice.
