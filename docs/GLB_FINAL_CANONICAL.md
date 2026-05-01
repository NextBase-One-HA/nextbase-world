# GLB Final Canonical Product Structure

STATE: CANONICAL_DRAFT_FIXED
GOAL: Define the completed product structure of GLB without mixing purchase pages, app body, private logic, and public UX.
BLOCKER: None.
IRREVERSIBLE: None. This document is a product/architecture canonical reference.

## 0. Core product truth

GLB exists to make the user understood anywhere.

Immutable product line:

> Be understood. Anywhere.

This is the root of the product. UI copy, routing, onboarding, dictionary logic, and monetization must not contradict it.

Final product definition:

```text
GLB is not just a translation app.
GLB is a mode-switching communication tool.
```

Modes:
- Core mode: daily communication.
- Travel mode: no-stuck travel communication.

## 1. Product roles

### GLB Core / 2.99

Role:
- Entry product.
- Daily translation utility.
- Fun, light, approachable.
- Users pay because it is useful and easy.

Meaning:
- "I want to use this often."

Primary page:
- `index.next.html`

Payment route:
- Stripe Core checkout.

### GLB Travel / 14.99

Role:
- Travel add-on / 30-day pass.
- Post-purchase travel tool.
- Calm, safe, no-stuck experience.
- Users pay because they do not want to fail in real-world situations.

Meaning:
- "I do not want to get stuck while traveling."

Primary app page:
- `index.14.99.html`

Purchase explanation page:
- `index.premium.html`

Important rule:
- `index.14.99.html` is the Travel app body after purchase.
- `index.premium.html` is the Travel Pass explanation and Stripe entrance.
- Purchase blocks must not be inserted into `index.14.99.html` unless the canonical route is intentionally changed.

Recovery exception:
- `index.14.99.html` may contain a small recovery link back to `index.premium.html` when a user lands there without a valid Travel state.
- This recovery link must be quiet and secondary.
- It must not become a sales block, pricing block, Stripe CTA, FAQ, or marketing section.

## 2. Correct user flow

### Normal Travel purchase flow

1. User uses or buys Core 2.99.
2. User sees Travel Pass explanation in `index.premium.html`.
3. User buys Travel Pass through Stripe.
4. Stripe success redirects to:
   - `index.14.99.html?session_id={CHECKOUT_SESSION_ID}&travel=1`
5. Travel app activates and stores entitlement state.
6. User uses Travel mode.

Canonical flow:

```text
User
  -> index.next.html / Core
  -> index.premium.html / Travel explanation
  -> Stripe Travel checkout
  -> index.14.99.html / Travel app body
```

### Direct admin/test flow

For internal test only:

```text
index.14.99.html?nori=admin
```

This does not define the public purchase route.

## 3. Page responsibilities

### `index.next.html`

Public role:
- Core 2.99 app body.
- Daily translation utility.
- Light and approachable entry point.
- Can lead subscribed users toward Travel explanation when relevant.

Meaning:
- Daily mode.

### `index.premium.html`

Public role:
- Explain Travel Pass.
- Explain 30-day access.
- Reduce uncertainty.
- Present Stripe checkout.
- Show FAQ, billing notes, refund/help links.
- Convert qualified Core users into Travel buyers.

Public copy should focus on:
- One-time 30-day travel pass.
- No recurring Travel charge.
- Be understood anywhere.
- Works for airport, taxi, hotel, restaurant, emergency.
- Instant access after checkout.

Allowed public elements:
- Price.
- Stripe checkout CTA.
- Payment explanation.
- FAQ.
- Support link.

Not allowed:
- App-only operational UI.
- Internal optimizer details.
- API cost language.
- Hidden routing language.

### `index.14.99.html`

Public role:
- Travel app body.
- Fast translation UI.
- Voice / Type / Phrases.
- Show result to another person.
- Maintain 30-day Travel Pass experience.

Meaning:
- Execution tool, not the main selling page.
- Minimal, focused, no wasted motion.

Primary public copy:

```text
When words fail
Be understood. Anywhere.
AI detects your travel scene.
Airport · Taxi · Hotel · Restaurant · Emergency
```

Allowed:
- Travel status.
- Language selector.
- Voice / Type / Phrases.
- Result stage.
- Flip for them.
- Travel expiration display.
- Minimal support link.
- Minimal recovery link to `index.premium.html` only when needed.

Not allowed by current canonical:
- Purchase block.
- Stripe checkout CTA.
- Marketing FAQ.
- Subscription sales copy.
- Large paywall block.

### `support.html`

Public role:
- Billing support.
- Cancellation/support guidance.
- Translation disclaimer.
- Privacy request channel.
- On-device dictionary notice.

Must include:
- Machine translation limitations.
- Stripe handles card/payment data.
- Travel Pass is one-time 30-day purchase.
- On-device personal dictionary notice.

## 4. Product layer model

```text
L1: User surface
  UI / copy / controls

L2: Experience
  fast response / scene feeling / safety

L3: Logic
  dictionary / quota / entitlement / translation

L4: Black box
  router / cost optimizer / provider / keys
```

Rules:
- L1 must be simple.
- L2 must feel premium.
- L3 must be reliable.
- L4 must stay internal.

## 5. Backend/service structure

Canonical runtime route:

```text
GLB UI
  -> Smile Friend Engine
  -> AI Router
  -> AI Provider
```

### Smile Friend Engine

Role:
- Public translation gate.
- Quota control.
- Billing entitlement check.
- Request forwarding to AI Router.

It is not the AI Router.

### AI Router

Role:
- Dedicated model/key/provider router.
- Resolves caller role.
- Uses `NB_GATE_PROD` for public GLB/Travel execution.
- Normalizes provider response into UI-safe output.
- Performs static cost optimizer before provider call.

Current canonical response shape:

```json
{
  "ok": true,
  "translatedText": "...",
  "model": "gemini-2.5-flash",
  "key_source": "NB_GATE_PROD",
  "provider_status": 200
}
```

For local optimizer hit:

```json
{
  "ok": true,
  "translatedText": "こんにちは",
  "model": "local-cache",
  "key_source": "LOCAL_CACHE",
  "provider_status": 200,
  "optimizer": "local_cache"
}
```

### AI Provider

Role:
- Actual model provider.
- Currently Gemini 2.5 Flash.
- Provider details must not leak into UI copy.

## 6. Public vs black-box rules

### Public to user

The user may see:
- Be understood. Anywhere.
- AI detects your travel scene.
- Voice / Type / Phrases.
- 30-day Travel Pass.
- Instant access.
- Cancel/manage support where applicable.
- On-device dictionary privacy notice.

### Not public / internal only

Never expose in product UI:
- API cost reduction.
- 0 yen / zero-cost route.
- Provider key routing.
- `NB_GATE_PROD` or other env names.
- Cache hit as a sales gimmick.
- Any language implying fake AI thinking.
- Any language implying hidden manipulation of quota.

Internal wording allowed in logs/docs:
- Cost Optimizer.
- local-cache.
- on-device dictionary.
- provider bypass.

## 7. On-device personal dictionary

Role:
- User-adaptive translation memory.
- Stored only on the user's browser/app storage.
- Improves repeated translation speed.
- Reduces unnecessary network requests.

Public framing:

```text
GLB can remember repeated phrases on your device so your travel phrases come back faster.
```

Internal framing:

```text
On-device dictionary reduces repeated API calls and improves perceived personalization.
```

Rules:
- Local-first only.
- No cloud sync unless explicit future consent exists.
- Language pair must be part of the dictionary key.
- Short/medium phrases only.
- Avoid saving long, sensitive, legal, medical, financial, or official documents.
- User can clear browser/app data to remove it.

Current implementation concept:

```text
key = from|to|normalized source phrase
value = translated phrase
```

Example:

```text
en|ja|i lost my bag -> バッグをなくしました。
```

## 8. Fuzzy / similar phrase matching

Role:
- Optional enhancement.
- Reuses local dictionary for very similar phrases.

Allowed only if safe:
- High confidence threshold.
- Same language pair.
- No negation.
- No sensitive/official text.

Examples:

```text
I lost my bag
I lost my luggage
```

Not allowed:

```text
I lost my bag
I did not lose my bag
```

Negation must block fuzzy reuse.

## 9. Onboarding language fixed model

Role:
- Reduce user confusion.
- Reduce repeated wrong-direction translation.
- Make GLB feel user-specific.

Rules:
- Detect browser language as initial base language.
- Save user base language locally.
- Save target language locally.
- Allow user to change it.
- Use saved pair as default next time.

Public framing:

```text
GLB remembers your usual language pair on this device.
```

Not public:
- Cost reduction from fewer retries.

## 10. Pricing and monetization boundary

### Core 2.99

- Monthly subscription.
- Cancel via Stripe Customer Portal.
- General usage / daily utility.

### Travel 14.99

- One-time 30-day Travel Pass.
- Not recurring.
- Bought through `index.premium.html`.
- Used through `index.14.99.html`.

Important:
- Do not confuse Core subscription and Travel Pass.
- Do not present Travel Pass as recurring if it is one-time.
- Do not put cancellation copy beside a non-recurring one-time Travel purchase unless wording is clear.

Preferred Travel wording:

```text
One-time checkout · 30-day access · Not recurring
```

## 11. Current rollback rule

Because the canonical flow uses `index.premium.html` as the purchase entrance:

Rollback from `index.14.99.html`:
- `glb-paywall`
- `start-pass-btn`
- `wireTravelPassCheckout`
- direct Stripe purchase block

Keep in `index.14.99.html`:
- AI scene copy.
- Voice / Type / Phrases.
- On-device dictionary.
- Language pair memory.
- Travel entitlement guard.
- Small recovery link only if it does not become a purchase block.

## 12. Acceptance checklist

### Premium page PASS

- Travel Pass explanation exists.
- Stripe Travel checkout works.
- Price and 30-day one-time terms are clear.
- FAQ/support exists.

### Travel app PASS

- After success redirect, Travel app opens.
- Voice / Type / Phrases buttons work.
- Language selectors are populated.
- Translation works through Smile Friend Engine -> AI Router.
- On-device dictionary saves repeated phrases.
- Travel app does not show purchase CTA in current canonical.
- If user lands invalidly, recovery route to premium is quiet and secondary.

### Cost optimizer PASS

- Static common phrases can return from AI Router local-cache.
- Repeated phrases can return from on-device dictionary.
- User-facing UI does not mention cost optimizer.

## 13. Final short canonical

```text
GLB is a mode-switching communication tool.
GLB Core 2.99 is the daily mode.
GLB Travel 14.99 is the 30-day no-stuck travel mode.
index.next.html is the Core app body.
index.premium.html sells and explains Travel Pass.
index.14.99.html is the post-purchase Travel app body.
A small recovery link from Travel to Premium is allowed only when the user is not validly activated.
Smile Friend Engine gates quota and billing.
AI Router handles model/key/provider routing and response normalization.
On-device dictionary personalizes repeated translations locally.
Cost optimizer is internal only.
Public truth: Be understood. Anywhere.
```
