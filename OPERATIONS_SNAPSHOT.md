# OPERATIONS SNAPSHOT

## Live Premise (Do Not Regress)
- Current production premise is **Render Static Site + GitHub Pages dual structure**.
- Reverting to server-runtime assumptions for the static frontend (for example, accidental Python build/runtime expectations on static deploy path) is prohibited.
- Any change that risks static deploy continuity must be treated as high risk and blocked until verified.

## Billing Guardrail Treaty (Inviolable)
- `LS_BILLING_LOCK` and `glb_subscribed` are mandatory, first-priority guardrails.
- Paid-user UI protection must run before visible render whenever possible (pre-hide strategy).
- Restoring free-tier UI for paid users ("quota", "subscribe upsell", or equivalent) is a prohibited regression.
- If API state and local paid lock diverge temporarily, do not downgrade paid UX prematurely.

## User Trust Route (Do Not Break)
- `index.next.html` Stripe management/cancel route is a trust-critical control surface.
- Do not hide, remove, or weaken cancel/manage subscription guidance.
- Billing self-service path must remain reachable and understandable to end users.

## Completion Evidence Policy
- "Done" claims without evidence are invalid.
- Completion reports must include at least one of:
  - commit hash, or
  - explicit behavioral proof (for example: which free-tier elements are removed/hidden and where).
- For billing-related edits, report verification outcomes for:
  - paid entry via `session_id`,
  - paid lock persistence,
  - unpaid redirect/guard behavior.

## Pre-Change Checklist (Short)
- Confirm target file role (free page vs paid page) before editing.
- Confirm billing guardrails are preserved (`LS_BILLING_LOCK`, `glb_subscribed`, paid pre-hide).
- Confirm Stripe manage/cancel route is still present for paid flow pages.

## Post-Change Verification Template
- `session_id` landing:
  - `glb_subscribed` updated to paid value.
  - `LS_BILLING_LOCK` present and preserved.
- Paid-flag-only revisit:
  - no free quota/subscribe flash.
  - paid access retained.
- Unpaid direct access:
  - redirected/guarded to free entry as designed.
- Cancel flow:
  - cancel/manage route visible.
  - lock-drop behavior unchanged where specified.

## Rollback Rule
- If paid users can see free-tier restrictions after successful pay-state, rollback/fix is immediate priority.
- Never trade billing correctness for new feature velocity.
