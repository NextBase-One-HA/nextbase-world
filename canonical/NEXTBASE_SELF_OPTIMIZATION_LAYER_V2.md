# NEXTBASE SELF OPTIMIZATION LAYER V2

This file is the mandatory entry point for all NextBase AI work.
It exists to prevent drift, old assumptions, and unsafe completion claims.

## Core direction
The source of truth controls the AI.
The AI does not control the source of truth.

```text
Canonical files
  -> AI / agent
  -> preflight
  -> response gate
  -> execution
  -> evidence
  -> GO or HOLD
```

## Required first-read files
Every AI or agent must read these before important work:

1. `canonical/NEXTBASE_CURRENT_STRUCTURE.md`
2. `canonical/NEXTBASE_SELF_OPTIMIZATION_LAYER_V2.md`
3. `ops/TOMORI_ZERO_TRUST_GATE.md`
4. `ops/GATEWAY_CANONICAL_GATE.md`

If chat memory conflicts with these files, these files win.

## Canonical names
Use only these names in normal work:

- GLB
- Smile Friend Engine
- translate
- AI Router

Old names may appear only as history, not as the working name.

## Current runtime structure
```text
User
  -> GLB
  -> Smile Friend Engine
  -> translate
  -> AI Router
  -> AI provider
  -> GLB
```

## Mandatory response shape
Every important report must include:

```text
STATE:
GOAL:
BLOCKER:
NEXT_ACTION:
EVIDENCE:
IRREVERSIBLE:
OUTPUT:
```

If any section is missing, the report is invalid.

## Stop words from NORI-san
If NORI-san says any of these, stop immediately:

- ズレ
- 違う
- ダメ
- HOLD
- rollback
- やめろ
- 止まれ

Then switch to HOLD and verify the source of truth.

## Completion rule
Never claim completion from local success only.
Never claim completion from merge only.
Never claim completion from deploy only.
Completion requires evidence from the final real target.

Examples:

- endpoint response
- logs
- tests
- GitHub merge state
- Cloud Run revision and behavior

## Release gate
Current GLB release remains HOLD until:

1. translate health shows gateway mode.
2. translate POST returns HTTP 200.
3. Smile Friend Engine request 1 to 5 returns HTTP 200.
4. Smile Friend Engine request 6 returns 429 FREE_LIMIT_REACHED.
5. Payment flow stays behind modal.
6. Cancellation flow explains before external portal.

## Short command
Read canonical first.
Check real state.
Show evidence.
Stop on drift.
Report GO or HOLD.
