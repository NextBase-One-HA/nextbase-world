# NEXTBASE_CURRENT_STATE

STATE: CURRENT_OK
DATE: 2026-05-03
MODE: NE_MODE_ACTIVE
PASSPHRASE: 刻の共振、法の静寂。

This file is the dynamic state snapshot for NextBase OS and GLB execution. Static law remains in `docs/NEXTBASE_SYSTEM_CANONICAL.md`. GLB product canon remains in `docs/GLB_FINAL_CANONICAL.md` and `docs/GLB_CHAT_BILLING_CANONICAL.md`.

## 1. Human authority

NORI-san retains final judgment, approval, stopping authority, and responsibility.
AI operates only as a support engine for proposal, analysis, generation, organization, and implementation assistance.

Rules:
- No autonomous irreversible execution.
- No unverified DONE declaration.
- No learning, evolution, or self-modification of the base model.
- Context understanding and memory are allowed only as external state/reference.
- If current state, canonical law, or latest instruction conflicts, transition to HOLD with securityLevel = 1.

## 2. NextBase layer model

Public structural model:

```text
Smile = entry
Core = internal processing
Friend = output
```

Operational layers:

```text
ORE    = human final judgment protection
TOMORI = structure, role assignment, shortest-route organization
STELLA = latest sync, canonical comparison, drift detection
NOIR   = evidence audit, log audit, abnormal stop
```

Execution arms:

```text
KURO   = documents, specifications, comparisons, practical writing
Cursor = implementation, corrections, technical work
```

KURO and Cursor do not directly decide or approve. NORI-san is the only hub.

## 3. Common execution frame

All execution reviews should use:

```text
STATE:
GOAL:
BLOCKER:
NEXT_ACTION:
EVIDENCE:
IRREVERSIBLE:
OUTPUT:
```

Common operation:
- Update by replacement, not uncontrolled append.
- Do not proceed on old assumptions.
- Do not claim completion without evidence.
- Irreversible actions wait for ORE approval.
- Latest snapshot has priority on restart.
- API is an internal tool; user-facing output must be prepared as Friend.

## 4. Confirmed NextBase OS implementation state

Confirmed in repository:
- `nextbase-api` gateway exists and injects canonical/inventory/context before forwarding to ai-router.
- Static canonical requires physical evidence for DONE.
- Firestore rooms exist for TTL room state.
- Firestore sessions exist for external memory/context.
- `agent_tasks` exists for evidence-gated task completion.
- `agent_violations` exists for DONE-rule violation visibility.
- `agent_reputation` exists for score, route class, and reputation ranking.

Current API code state:

```text
api_version = 1.3.7
Gateway includes:
- SYSTEM_CANONICAL_LAW
- SYSTEM_INVENTORY
- DONE_RULE
- REPUTATION
- SESSION_CONTEXT
- OPEN_AGENT_TASKS
- RECENT_VIOLATIONS
```

Evidence-gated DONE:

```text
DONE = git_commit + deploy_revision + test_command + test_response
Missing evidence = HOLD
```

Reputation economy:

```text
verified DONE = +10 score
DONE violation = -20 score
score >= 50 = normal
score < 50 = restricted
score <= 0 = blocked
```

Current limitation:
- Latest repository changes after api_version 1.3.7 still require Cloud Run deployment and physical curl verification before REALITY_DONE.

## 5. GLB product truth

GLB is not just a translation app. GLB is a mode-switching communication tool.

Public product line:

```text
Be understood. Anywhere.
```

Core product:

```text
GLB Core = $2.99 monthly subscription
Role: daily translation access and room joining
```

Travel product:

```text
GLB Travel = $14.99 one-time 30-day Travel Pass
Role: create a 30-day Translation Room and use Travel mode
```

Room rule:

```text
Travel $14.99 purchaser can create a 30-day limited chat room.
GLB Core $2.99 purchaser can join a room and use translation chat.
Free users cannot create or use room chat until entitlement is valid.
```

Room lifetime:

```text
min(30 days from creation, host Travel expiry)
```

Product boundary:
- No permanent social network.
- No phonebook integration.
- No public user search.
- No long-term chat history.
- Temporary room is the value.

## 6. Billing and entitlement target

Billing truth must be server-side only.

Required API surface for monetization:

```text
GET  /entitlements
POST /billing/core/checkout        # Core $2.99 monthly
POST /billing/travel/checkout      # Travel $14.99 one-time 30 days
POST /billing/webhook              # Stripe source of truth
POST /rooms/create                 # requires travel_active=true
POST /rooms/join                   # requires core_subscribed or travel_active
POST /rooms/{room_id}/messages     # requires active room participant
GET  /rooms/{room_id}/messages     # active room only
POST /translate                    # room-aware translation endpoint
```

Implementation status:
- Existing repository has `/rooms/create`, `/rooms/join`, `/rooms/message`, `/rooms/status` minimal TTL APIs.
- Billing/entitlement APIs are canonical but not yet confirmed implemented in `nextbase-api`.
- Room chat message endpoint shape needs GLB canonical alignment.
- `/translate` room-aware product endpoint still needs implementation.

## 7. Immediate GLB build priority

Priority is revenue, not unlimited OS expansion.

Next build order:
1. Server-side `/entitlements` for Core/Travel access.
2. Stripe checkout + webhook for Core $2.99 and Travel $14.99.
3. Enforce room creation only for Travel active users.
4. Enforce room joining only for Core or Travel users.
5. Add room-aware `/translate`.
6. Connect minimal Travel Room UI.
7. Verify with physical evidence: git_commit, deploy_revision, test_command, test_response.

HOLD condition:
- If billing truth is only localStorage, HOLD.
- If Travel app can create room without server entitlement, HOLD.
- If Core user cannot join after valid entitlement, HOLD.
- If room becomes permanent/social graph, HOLD.

## 8. Current strategic focus

NORI-san's current goal:
- Build a user-specific, travel-specific translation app to create living income.
- Use 30-day Travel Room as the monetizable core.
- Do not let patent work distract GPT from OS/product execution.

Division of labor:
- Gemini team: patent filing/corrections and drafting support.
- GPT/NextBase OS review: architecture, product boundary, implementation state, evidence, and revenue path.

## 9. Restart declaration status

Self-Optimization Layer restarted under NE mode.

Meaning:
- Optimize only for NORI-san's current task and path.
- Avoid irreversible wrong progress.
- Use future calculation to show possible paths without taking final authority.
- If drift is detected, HOLD/rollback before further execution.

End state:

```text
NextBase OS focus = GLB Travel monetization path.
Immediate target = paid 30-day Travel Room with server-side entitlement.
```
