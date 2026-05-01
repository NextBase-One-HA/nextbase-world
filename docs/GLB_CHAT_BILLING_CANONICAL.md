# GLB Chat + Billing Canonical Structure

STATE: CANONICAL_FIXED
GOAL: Fix the product structure for GLB onboarding, Core, Travel, 30-Day Translation Room, chat, and billing control.
BLOCKER: None.
IRREVERSIBLE: None. This is the implementation reference for Gemini/Cursor/GPT review.

---

## 1. Product truth

GLB is not just a translation app.
GLB is a mode-switching communication tool.

Public truth:

```text
0 seconds to connect.
Be understood. Anywhere.
```

Internal truth:

```text
Core = daily translation access.
Travel = 30-day travel communication mode.
Room = temporary translation chat bridge.
Billing = server-side only.
```

---

## 2. Page roles

### index.html

Role:
- Language gate.
- Onboarding.
- Emotional first impression.
- Saves base language.

Allowed CTAs:
- Try free - 5 translations/day -> index.next.html
- GLB Core - $2.99 -> Core Stripe checkout

Not allowed:
- Direct Travel $14.99 purchase CTA.
- Travel app launch.
- Chat room creation.

Reason:
- Onboarding must not skip the Core funnel.

### index.next.html

Role:
- Free trial / 5 translations per day.
- Cloud quota ready.
- Shows upgrade path to Core $2.99.

Allowed:
- Free translation.
- Core purchase CTA.
- Light Travel mention only after quota wall.

Not allowed:
- Unlocking paid state by localStorage only.
- Creating rooms.

### index.2.99.html

Role:
- Core paid app body.
- Daily translation utility.
- Core users can join Translation Rooms.

Allowed:
- Unlimited Core translation after entitlement check.
- Join Room button.
- Room code input.
- Language setting return link.

Not allowed:
- Create Room.
- Travel purchase block as the main UI.
- Client-side paid unlock.

### index.premium.html

Role:
- Travel Pass explanation and purchase page.
- Main sales page for Travel $14.99.

Allowed:
- 30-Day Translation Room explanation.
- Travel checkout CTA.
- One-time 30-day access explanation.
- FAQ/support.

Not allowed:
- App body.
- Chat execution UI.

### index.14.99.html

Role:
- Travel app body after purchase.
- Travel user can create 30-day Translation Rooms.

Allowed:
- Create Room button.
- Share Code / Share Link.
- Travel translation UI.
- Small recovery link to premium only when entitlement invalid.

Not allowed:
- Large purchase block.
- Stripe sales block.
- Marketing FAQ.

### glb-room.html

Role:
- Shared Translation Room UI.

Modes:
- `?mode=create` = Travel host creates room.
- `?mode=join` = Core or Travel user joins room.

Allowed:
- Create code UI.
- Join code UI.
- Chat UI.
- Temporary translation chat.

Not allowed:
- Phonebook integration.
- Public user search.
- Permanent social graph.
- Long-term chat history.

---

## 3. Billing truth

Billing must be server-side.

```text
UI
  -> Smile Friend Engine
      -> Stripe / entitlement DB
      -> quota / access gate
  -> AI Router
```

Frontend may store only helper identifiers:

```text
glb_client_id_v1
glb_customer_id or GLB_CUSTOMER_ID
glb_last_entitlement_check
```

Frontend must not store the source of truth:

```text
core_paid=true
travel_paid=true
travel_active=true
room_host=true
```

Those values are display cache only and must be overridden by server entitlements.

---

## 4. Entitlement response

Canonical `/entitlements` response:

```json
{
  "ok": true,
  "customer_id": "cus_xxx",
  "core_subscribed": true,
  "travel_active": false,
  "travel_pass_expires_at": null,
  "room_create_allowed": false,
  "room_join_allowed": true,
  "subscription_status": "active",
  "billing_grace": false
}
```

Rules:
- `core_subscribed=true` allows Core app and Join Room.
- `travel_active=true` allows Travel app and Create Room.
- `travel_pass_expires_at` is server canonical.
- Local 30-day timers are only fallback/display.

---

## 5. Stripe rules

### Core $2.99

Type:
- Monthly subscription.

Webhook:
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

Server result:

```text
core_subscribed = true/false
```

### Travel $14.99

Type:
- One-time 30-day pass.

Webhook:
- `checkout.session.completed`

Server result:

```text
travel_active = true
travel_pass_started_at = now
travel_pass_expires_at = now + 30 days
```

Travel expiry must be enforced server-side.

---

## 6. Room permissions

### Travel user

Can:
- Create room.
- Share room code/link.
- Chat inside active room.

Cannot:
- Extend room beyond Travel expiry unless buying another Travel Pass.

### Core user

Can:
- Join room using code/link.
- Chat inside active room.

Cannot:
- Create room.

### Free user

Can:
- See join/create preview.
- Be asked to buy Core before joining.

Cannot:
- Use room chat.
- Create room.

---

## 7. Room lifetime

Room lifetime:

```text
min(30 days from creation, host Travel expiry)
```

Room must expire automatically.

No room may become permanent.
No room may become a social network.
No user search.
No phonebook.
No persistent identity required.

Room identity:

```text
room_id
room_code
host_customer_id
created_at
expires_at
status
```

Participant identity:

```text
room_id
customer_id or client_id
role: host/member
base_lang
target_lang
joined_at
```

---

## 8. Chat rules

Chat v1:
- Two participants preferred.
- Temporary messages.
- Translation per message.
- Same AI Router path as normal translation.
- NE Gate may hold risky messages before delivery.

Message storage:
- Short retention only while room is active.
- No long-term chat history.
- No public profile.

Message schema:

```text
message_id
room_id
sender_id
source_lang
target_lang
source_text
translated_text
created_at
risk_state: pass/hold
```

Public copy:

```text
The room exists for 30 days.
Only people with the code can enter.
```

Do not say:

```text
Your conversations stay forever.
```

Correct replacement:

```text
The room disappears after 30 days — that is what makes it real.
```

Japanese:

```text
ルームは30日で消える — だから、その会話は濃くなる。
```

---

## 9. API surface v1

Minimum backend API:

```text
GET  /entitlements?customer_id=... or session_id=...
POST /rooms/create
POST /rooms/join
GET  /rooms/{room_id}
POST /rooms/{room_id}/messages
GET  /rooms/{room_id}/messages
```

Access rules:
- `/rooms/create` requires `travel_active=true`.
- `/rooms/join` requires `core_subscribed=true` or `travel_active=true`.
- `/messages` requires active room and valid participant.

---

## 10. Visual system

Three visual layers:

```text
index.html      = emotion / smile / future
index.2.99.html = function / fast / usable
index.14.99.html = world / travel / connection
```

Image rules:
- Generated images are preferred over stock images.
- Images must be UI-first.
- Center must have empty space.
- Bottom must be dark enough for text.
- Do not put background image on body.
- Scope background to hero/stage only.

Core page rule:
- `hero_299.jpg` belongs inside `#glb-result-stage` only.

Onboarding rule:
- `hero_onboarding.jpg` belongs inside `.ip-hero` only.

Travel rule:
- `hero_travel.jpg` belongs inside Travel hero/stage only.

---

## 11. Language setting

Every public page should include a small language reset/change link.

Action:

```javascript
localStorage.removeItem('glb_ui_lang');
location.href = 'index.html';
```

This returns the user to language gate.

Must preserve:
- Billing state identifiers.
- Customer/session IDs.
- Client ID.

Do not clear all localStorage for language reset.

---

## 12. Gemini / Cursor / GPT workflow

### Gemini

Use for:
- Draft implementation plan.
- UI block generation.
- Backend scaffolding suggestions.

Do not allow Gemini to:
- Rewrite full files blindly.
- Change billing truth.
- Change canonical page roles.
- Expose black-box internals.

### Cursor

Use for:
- Actual code edits.
- File patching.
- Git operations.
- Syntax checks.

Cursor must follow this canonical doc.

### GPT

Use for:
- Final architecture review.
- Safety and product boundary review.
- Patch correction.
- Canonical consistency check.

Final rule:

```text
Gemini drafts.
Cursor implements.
GPT reviews and corrects.
Nori decides.
```

---

## 13. Implementation order

1. Fix canonical docs.
2. Fix onboarding CTAs.
3. Fix Core 2.99 visual/stage background.
4. Add language reset links.
5. Server-side Travel expiry field.
6. Finalize `/entitlements` response.
7. Create `glb-room.html` UI only.
8. Add room backend.
9. Add chat UI.
10. Connect room chat to AI Router.

Do not build chat backend before page roles and billing boundaries are stable.

---

## 14. Final short canonical

```text
index.html = language gate and onboarding.
index.next.html = free 5/day trial.
index.2.99.html = Core paid app; can Join Room.
index.premium.html = Travel sales page.
index.14.99.html = Travel app; can Create Room.
glb-room.html = 30-day Translation Room and chat UI.
Core $2.99 = join rooms.
Travel $14.99 = create rooms for 30 days.
Billing and entitlement truth lives on Smile Friend Engine.
Frontend is display only.
No phonebook. No user search. No permanent chat history.
```
