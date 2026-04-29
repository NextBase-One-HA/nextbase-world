# smile-friend-engine (Cloud Run)

Service name: **`smile-friend-engine`**  
Project: **`nb-official-base`**  
Region: **`us-central1`**

## Server-side free quota

`/translate` enforces **5 requests per UTC day per `client_id`** (unless paid bypass via billing). The **6th** unpaid request returns **429** with `reasonCode: FREE_QUOTA_EXCEEDED`.

## Configure translate execution (pick one)

1. **In-process (recommended if translate already lives in this service)**  
   Set **`GLB_TRANSLATE_CALLABLE`** to an async function:

   `mypackage.module:run_translate`

   Signature:

   `async def run_translate(raw: bytes, content_type: str, body_json: dict) -> starlette.responses.Response`

   Wire your existing Gemini / Vertex translate logic there. **No extra HTTP hop.**

2. **Optional HTTP proxy** (only if you intentionally split translate to another base URL)  
   Set **`TRANSLATE_UPSTREAM_URL`** — requests are forwarded to `{TRANSLATE_UPSTREAM_URL}/translate`.

Priority: **`GLB_TRANSLATE_CALLABLE`** first, then **`TRANSLATE_UPSTREAM_URL`**.

## Other env vars

| Variable | Purpose |
|----------|---------|
| `GLB_FREE_QUOTA_DB_PATH` | SQLite file for daily counts — **use a mounted volume** on Cloud Run; `/tmp` is ephemeral. |
| `GLB_FREE_DAILY` | Default `5`. |
| `BILLING_ENTITLEMENTS_BASE` | Billing service origin; optional paid bypass via `GET /entitlements?customer_id=` |

## Build

From repo root:

```bash
docker build -f cloud_run/smile-friend-engine/Dockerfile -t smile-friend-engine:local .
```

## Deploy (example)

Adjust image registry and secrets as needed:

```bash
gcloud run deploy smile-friend-engine \
  --project nb-official-base \
  --region us-central1 \
  --image REGION-docker.pkg.dev/nb-official-base/.../smile-friend-engine:latest \
  --set-env-vars GLB_FREE_DAILY=5,BILLING_ENTITLEMENTS_BASE=https://your-billing-url.run.app \
  --set-secrets ...
```

Add a **persistent volume** mapping for `GLB_FREE_QUOTA_DB_PATH` so quota survives restarts.
