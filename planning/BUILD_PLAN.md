# Seven-day build plan

Dates are based on the published 28 August–4 September 2026 window. Replace
relative deadlines with the organizer's exact Europe/London timestamps after
kickoff.

## Definition of demo-ready

By the end of Day 2, a fresh clone must support one human-triggered flow from a
synthetic evidence packet to a schema-valid proposal, deterministic verdict,
and visible audit trace. Alpaca paper submission may still be stubbed on Day 2,
but the trust boundary must already be real.

## Day 1 — rules, repository, skeleton

- Capture kickoff rules and resolve the rules ledger.
- Obtain explicit approval for the final public boundary and licence.
- Create the new public repository with clean history.
- Add README, licence, security notes, paper-only disclaimer, `.gitignore`, and
  `.env.example` containing names only.
- Establish backend/frontend skeleton, CI, health endpoint, and tests.
- Implement the versioned proposal schema and synthetic evidence fixture.

Gate: clean clone starts locally; secret scan and licence inventory pass.

## Day 2 — vertical slice

- Implement one AI provider behind a narrow interface.
- Validate structured output and bounded user-visible rationale.
- Implement deterministic gates and stable reason codes.
- Persist an append-only decision record.
- Render the evidence/proposal/verdict trace.

Gate: approved, resized, rejected, malformed, and provider-timeout cases pass
without any broker dependency.

## Day 3 — Alpaca paper integration

- Verify paper account and endpoint before every submission.
- Implement asset/account/position reads and paper order submission.
- Use deterministic client order IDs and reconcile unknown outcomes.
- Add duplicate protection and broker-error tests.

Gate: one small paper order is submitted and reconciled end to end; ambiguous
mode or response fails closed.

## Day 4 — product demonstration

- Build the primary approved/resized scenario.
- Build the deterministic rejection scenario.
- Add kill switch and paper-only status treatment.
- Add synthetic replay fallback.
- Make the trace understandable without narration.

Gate: an unfamiliar reviewer can explain the product after a two-minute demo.

## Day 5 — hosting and hardening

- Deploy the public application using the event-accepted platform.
- Configure secrets outside source control.
- Test signed-out access, cold start, API failure, market-closed behaviour, and
  mobile/desktop layout.
- Run dependency, licence, secret, and repository-history checks.

Gate: hosted demo works from a private browser session and leaks no sensitive
data.

## Day 6 — presentation

- Capture stable demo footage.
- Produce the PDF deck and 16:9 cover image.
- Draft final short/long descriptions and technology tags.
- Record a video no longer than five minutes.
- Ask a mentor one precise question about positioning or eligibility.

Gate: a complete mock submission exists and every link is accessible.

## Day 7 — freeze and submit

- Freeze features at least 12 hours before the normal deadline.
- Run tests from a clean clone and verify the hosted revision matches it.
- Recheck paper-only safety, secrets, licence, and dependency notices.
- Watch the final video and inspect every deck page.
- Submit early, then verify the saved submission fields and URLs.
- Preserve the exact submitted commit SHA and evidence screenshots.

Gate: submission confirmed before the normal deadline.

## Scope-cut order

Cut from the bottom upward if schedule slips:

1. Multiple AI providers.
2. Multiple strategies or asset classes.
3. Automated scheduling.
4. Rich performance analytics.
5. News ingestion beyond one bounded source.
6. Advanced portfolio optimization.
7. Authentication and multi-user features.

Never cut:

- Paper-only enforcement.
- Deterministic risk authority.
- Schema validation.
- Idempotency/reconciliation.
- Approved and rejected demo paths.
- Audit trace.
- Public clean-clone usability.
- Submission media and deadline buffer.

## Stop conditions

- If the organizer disallows the proposed pre-existing-code posture, implement
  cleanly without copying Profit Goblin code.
- If account mode cannot be proven paper-only, disable submission and demo the
  synthetic replay.
- If an order result is ambiguous, reconcile; do not retry blindly.
- If a dependency or asset licence is unresolved, remove or replace it.
- If the public tree contains private material, stop publication until the
  candidate is clean and reviewed.
- If a feature threatens the submission deadline, apply the scope-cut order.
