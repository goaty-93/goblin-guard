# Kickoff checklist

Use this checklist immediately after the official kickoff on 28 August 2026.
Do not create the public repository or implement competition functionality
before resolving the event-specific gates.

## Capture

- Save the event page, challenge text, schedule, rules, sponsor resources, and
  submission requirements with timestamps.
- Record the exact Europe/London submission deadline.
- Record any mandatory technology, model, MCP, CLI, build-in-public, or licence
  requirement.
- Save the organizer's answers about pre-existing scaffolding, MIT licensing,
  Trading API eligibility, and the unrelated IBM Bob text.
- Record prize tracks and any special judging criteria.

## Decide

- Confirm whether direct Alpaca Trading API is sufficient.
- Confirm whether the public repository must be created after kickoff.
- Confirm the allowed pre-existing-code posture.
- Confirm the exact open-source licence.
- Confirm whether scheduled autonomy is expected.
- Confirm the hosted-demo platform.
- Confirm the AI model and reasoning setting after a small representative eval.

## Public-boundary review

- Approve the new repository name and owner.
- Review the exact planned initial tree.
- Confirm no Profit Goblin Git history, source, database, exports, screenshots,
  credentials, infrastructure, or private research will enter it.
- Confirm synthetic fixtures contain fictional data only.
- Prepare `.gitignore`, `.env.example` with names only, licence, README,
  security notes, and attribution notices.

## Account readiness

- Create or select dedicated Alpaca paper credentials; do not reuse Profit
  Goblin credentials.
- Create a dedicated OpenAI API project/key with a small explicit budget.
- Create the chosen hosting account/project.
- Store secrets outside Git and verify they can be rotated.
- Do not paste any credential into chat or planning documents.

## Start authorization

Implementation may begin only when:

- Event-specific rules are captured.
- Eligibility questions are resolved or the clean-room fallback is selected.
- Public boundary and licence are approved.
- Paper-only architecture remains intact.
- Day 1 scope and stop conditions are understood.

If any critical rule remains unanswered, implement only original clean-room
code during the event and copy nothing from Profit Goblin.
