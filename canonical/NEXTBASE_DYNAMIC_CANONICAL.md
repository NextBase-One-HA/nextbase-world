# NEXTBASE DYNAMIC CANONICAL

This file records the current moving state toward `canonical/NEXTBASE_IMMUTABLE_CANONICAL.md`.
It can change as implementation changes.
It cannot override the immutable canonical.

## Current status

```text
STATE: HOLD
GOAL: Make GLB work as the first revenue product inside NextBase OS.
BLOCKER: AI Router credential usage is still returning expired key error.
NEXT_ACTION: Fix AI Router credential read path and verify endpoint returns HTTP 200.
OUTPUT: HOLD until real endpoint evidence passes.
```

## Current runtime target

```text
User
  -> GLB
  -> Smile Friend Engine
  -> AI Router
  -> AI provider
  -> GLB
```

## Adapter path (non-primary)

```text
Smile Friend Engine
  -> translate
  -> AI Router
```

## Current service map

```text
GLB UI:
  GitHub Pages / static HTML files

Smile Friend Engine:
  Cloud Run service: smile-friend-engine
  Region: us-central1
  Role: human-side entrance/exit, quota, entitlement, STELLA checks

translate:
  Cloud Run service: translate
  Region: us-central1
  Role: fallback / test / compatibility adapter to AI Router

AI Router:
  Cloud Run service: nextbase-gateway-v1
  Region: asia-northeast1
  Role: AI-side routing and provider control

nextbase-app:
  Cloud Run service exists
  Role not fully finalized in current GLB route
```

## Confirmed facts

- Path mismatch between translate and AI Router was fixed.
- translate `/health` returns gateway_v1_configured true.
- translate POST reaches AI Router `/translate`.
- Remaining error is provider-level API key expired.
- AI Router uses NB_GATE_PROD in code.

## Current release gate

HOLD until all pass:

1. AI Router `/translate` returns HTTP 200.
2. translate POST `/translate` returns HTTP 200.
3. Smile Friend Engine requests 1 to 5 return HTTP 200.
4. Smile Friend Engine request 6 returns HTTP 429 with `FREE_LIMIT_REACHED`.
5. GLB UI uses Smile Friend Engine route correctly.
6. Payment flow still routes through modal.
7. Cancellation flow explains before external portal.

## Immediate technical priority

```text
1. Confirm AI Router reads NB_GATE_PROD correctly.
2. Ensure NB_GATE_PROD is valid and not expired.
3. Verify genai.Client(api_key=...) uses NB_GATE_PROD.
4. Re-test endpoint until HTTP 200 is achieved.
```

## Naming rule

Use:

- GLB
- Smile Friend Engine
- STELLA
- translate
- AI Router
- Self Optimization Layer
- Proof Mode

## Evidence rule

No GO from:

- local code only
- branch only
- merge only
- deploy only

GO candidate requires real endpoint evidence.

## Short form
Immutable canonical points.
Dynamic canonical moves.
translate is now adapter only.
Primary path is Smile Friend Engine -> AI Router.
Current state is HOLD until endpoint proof passes.
