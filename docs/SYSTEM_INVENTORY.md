# SYSTEM_INVENTORY

STATE: INVENTORY_OK

Inventory reference for gateway HOLD checks. Services and keys are named only; secrets are never stored in-repo.

## Routing

- **nextbase-api** — mandatory canonical injection + `/gateway`
- **ai-router** — upstream LLM routing (address via `TRANSLATE_UPSTREAM_URL` only in deployment env)

## Canonical references (read every request)

- `docs/NEXTBASE_SYSTEM_CANONICAL.md` — static law (DONE_RULE, gateway enforcement) fileciteturn433file0
- `docs/NEXTBASE_CURRENT_STATE.md` — dynamic OS state, NE mode, GLB execution snapshot
- `docs/GLB_FINAL_CANONICAL.md` — GLB product definition and UI/UX boundary fileciteturn436file0
- `docs/GLB_CHAT_BILLING_CANONICAL.md` — chat, room, billing, entitlement truth fileciteturn438file0

Gateway must treat:

```text
SYSTEM_CANONICAL = law
CURRENT_STATE    = latest execution truth
GLB_CANONICAL    = product truth
CHAT_BILLING     = monetization and room truth
```

## Operations

Rotations and env updates are done out-of-band; gateway reads this file each request (no reliance on remote chat history). Audit failure markers are documented only in ops runbooks, not in free text that could false-trigger automation.
