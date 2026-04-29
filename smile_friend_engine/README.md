# Smile Friend Engine — server-side free quota

This package adds **per-`client_id` daily limits** on `POST /translate` before proxying to your existing translate implementation.

## Environment

| Variable | Purpose |
|----------|---------|
| `GLB_QUOTA_BACKEND` | `firestore` (default when `GOOGLE_CLOUD_PROJECT` is set) or `sqlite` for local/tests |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Firestore |
| `GLB_FIRESTORE_QUOTA_COLLECTION` | Collection name (default `quotas`) |
| `GLB_FREE_QUOTA_DB_PATH` | SQLite path when `GLB_QUOTA_BACKEND=sqlite` |
| `GLB_FREE_DAILY` | Max free translations per UTC day (default `5`) |
| `GLB_TRANSLATE_CALLABLE` | **Preferred:** `package.module:async_func` — in-process translate after quota. Signature: `(raw, content_type, body_json) -> Response`. No extra microservice. |
| `TRANSLATE_UPSTREAM_URL` | **Optional** proxy: `{base}/translate` only if you already split translate to another URL. |
| `BILLING_ENTITLEMENTS_BASE` | Optional. If set (e.g. `https://your-billing.run.app`), `customer_id` in the JSON body is checked via `GET /entitlements?customer_id=...`. When `core_subscribed` or `travel_active` is true, **no quota** is applied. |

### Firestore schema (`quotas`)

- Document id: `client_id` (UUID string)
- Fields: `count` (int), `lastResetDate` (`YYYY-MM-DD` UTC date string)
- When `lastResetDate` ≠ today, count is reset for the limit check, then incremented for the allowed request.

## Request JSON (from GLB web)

- `client_id` (required): UUID in `glb_client_id_v1` (localStorage).
- `customer_id` (optional): Stripe `cus_...` when known; enables paid bypass when billing returns active entitlements.
- `text`, `source`, `target`, `caller_id`: unchanged.

## Response

- **429** with `{ "error": "FREE_LIMIT_REACHED" }` when the free daily cap is reached.

## Deploy options

1. **Sidecar / new service**: Run this app as the public URL; set `TRANSLATE_UPSTREAM_URL` to the previous internal translate base URL.
2. **Merge**: Import `translate_quota_gate` and `forward_to_upstream` from `smile_friend_engine.main` and call the gate **before** your existing translate handler.

Do not change Stripe payment links or GLB purchase flows in the HTML; this service only enforces free-tier usage on `/translate`.
