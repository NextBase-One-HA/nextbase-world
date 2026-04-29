# GATEWAY CANONICAL GATE

## Purpose
Prevent translate work from bypassing the canonical NextBase gateway path.

## Canonical route
```text
client -> smile-friend-engine -> translate -> nextbase-gateway-v1 -> provider
```

## Role mapping
```text
noir  -> NB_GATE_NOIR
admin -> NB_GATE_ADMIN
dev   -> NB_GATE_DEV
prod  -> NB_GATE_PROD
```

## Forbidden
- Do not bypass nextbase-gateway-v1 unless NORI-san explicitly approves emergency mode.
- Do not use admin role as production fallback.
- Do not treat all roles as the same level.
- Do not ask for credential re-entry before checking actual Cloud Run environment and route.
- Do not diagnose provider auth errors before checking whether the route bypasses the gateway.

## Required check before translate changes
```bash
bash tools/tomori_preflight.sh

gcloud run services describe translate --project nb-official-base --region us-central1

gcloud run services describe nextbase-gateway-v1 --project nb-official-base --region asia-northeast1
```

## HOLD condition
If translate fails while prod role is already configured, stop.
Do not request re-entry.
Check the route first.

## Short form
Gateway first.
No role bypass.
No admin fallback.
No credential re-entry before route check.
