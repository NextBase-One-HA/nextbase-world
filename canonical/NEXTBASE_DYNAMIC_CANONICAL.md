# NEXTBASE DYNAMIC CANONICAL

This file records the current moving state toward `canonical/NEXTBASE_IMMUTABLE_CANONICAL.md`.
It can change as implementation changes.
It cannot override the immutable canonical.

## Current status

```text
STATE: HOLD
GOAL: Make GLB work as the first revenue product inside NextBase OS through the dedicated AI Router.
BLOCKER: GLB UI route, payment modal path, and cancellation flow still need live verification.
NEXT_ACTION: Verify GLB UI live behavior, then verify payment and cancellation flows.
OUTPUT: HOLD until GLB UI and revenue/user-facing flows pass live evidence.
```

## Correct production target

```text
User
  -> GLB
  -> Smile Friend Engine
  -> AI Router dedicated service
  -> AI provider
  -> GLB
```

## Current service map

```text
GLB UI:
  GitHub Pages / static HTML files
  index.14.99.html: unfinished candidate, API origin points to Smile Friend Engine, caller_id=travel is valid through AI Router

Smile Friend Engine:
  Cloud Run service: smile-friend-engine
  Region: us-central1
  URL: https://smile-friend-engine-125142687526.us-central1.run.app
  Status: LIVE_PASS for upstream to dedicated AI Router and free quota gate

AI Router dedicated service:
  Cloud Run service: ai-router
  Region: asia-northeast1
  URL: https://ai-router-125142687526.asia-northeast1.run.app
  Status: LIVE_PASS
  caller_id roles: prod/travel/glb -> NB_GATE_PROD; dev -> NB_GATE_DEV; admin -> NB_GATE_ADMIN; noir -> NB_GATE_NOIR

nextbase-gateway-v1:
  Legacy compatibility / rollback only.

translate:
  fallback / test / compatibility adapter only.

NextBase API:
  Created by user report, HOLD until endpoint evidence proves role and usability.
```

## Confirmed facts

- Dedicated AI Router `/translate` returned HTTP 200.
- Dedicated AI Router used `model=gemini-2.5-flash`.
- Dedicated AI Router returned `key_source=NB_GATE_PROD` and `provider_status=200`.
- `caller_id=travel` also returned HTTP 200 with `key_source=NB_GATE_PROD` and `provider_status=200`.
- Smile Friend Engine was pointed to dedicated `ai-router` via `TRANSLATE_UPSTREAM_URL`.
- Smile Friend Engine `/translate` returned HTTP 200 through dedicated AI Router.
- Smile Friend Engine quota test passed: requests 1-5 returned HTTP 200, request 6 returned HTTP 429 with `FREE_LIMIT_REACHED`.
- `index.14.99.html` resolves API origin to Smile Friend Engine and sends UUID `client_id`.

## Current release gate

HOLD until all pass:

1. Dedicated AI Router `/translate` returns HTTP 200 with `key_source=NB_GATE_PROD`. PASS.
2. Dedicated AI Router supports `caller_id=travel` -> `NB_GATE_PROD`. PASS.
3. Smile Friend Engine is pointed to dedicated AI Router. PASS.
4. Smile Friend Engine requests 1 to 5 return HTTP 200. PASS.
5. Smile Friend Engine request 6 returns HTTP 429 with `FREE_LIMIT_REACHED`. PASS.
6. GLB UI `index.14.99.html` live behavior is verified in browser/device.
7. Payment flow still routes through modal.
8. Cancellation flow explains before external portal.
9. NextBase API role and usable endpoint evidence are verified if it is part of the release route.

## Immediate technical priority

```text
1. Finish index.14.99.html UI.
2. Verify browser/device translation flow through Smile Friend Engine.
3. Verify payment flow still routes through modal.
4. Verify cancellation flow explains before external portal.
5. Record evidence in execution ledger.
```

## Evidence rule

No GO from memory, local code only, merge only, deploy only, or API creation alone.
GO candidate requires real endpoint, browser/device, file, log, test, screenshot, or human real-device evidence.

## Short form
Dedicated AI Router is LIVE_PASS.
Travel caller route is LIVE_PASS.
Smile Friend Engine upstream and quota are LIVE_PASS.
Primary path is GLB -> Smile Friend Engine -> dedicated AI Router.
Current state is HOLD until GLB UI and revenue/user-facing flows pass proof.
