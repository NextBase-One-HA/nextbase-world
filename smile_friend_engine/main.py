"""
Cloud Run translate entry with server-side free-tier quota.

Deploy with:
  GLB_FREE_QUOTA_DB_PATH      SQLite path (persisted volume recommended on Cloud Run)
  GLB_FREE_DAILY              Default 5
  BILLING_ENTITLEMENTS_BASE   Billing service origin for paid bypass (optional)
  GLB_TRANSLATE_CALLABLE      Preferred: ``module.path:async_fn`` in-process translate (no extra service)
  TRANSLATE_UPSTREAM_URL      Optional proxy to ``{url}/translate`` only if you already split translate

Free quota: ``client_id`` (UUID) per UTC day; 6th unpaid request → 429 ``{"error":"FREE_LIMIT_REACHED"}``.
Storage: Firestore collection ``quotas`` (or SQLite if ``GLB_QUOTA_BACKEND=sqlite``).

Integrate into an existing app by importing ``translate_quota_gate`` and calling it
before your translate handler.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from smile_friend_engine.paid_check import customer_is_unlimited
from smile_friend_engine.quota_backend import quota_backend_name
from smile_friend_engine.quota_firestore import try_increment_free_quota as fs_try_increment
from smile_friend_engine.quota_sqlite import SqliteDailyQuota
from smile_friend_engine.translate_dispatch import dispatch_translate

FREE_DAILY = int(os.getenv("GLB_FREE_DAILY", "5"))
DB_PATH = os.getenv("GLB_FREE_QUOTA_DB_PATH", "/tmp/glb_free_quota.sqlite3")

_quota_sqlite: Optional[SqliteDailyQuota] = None


def _sqlite_store() -> SqliteDailyQuota:
    global _quota_sqlite
    if _quota_sqlite is None:
        _quota_sqlite = SqliteDailyQuota(DB_PATH)
    return _quota_sqlite


async def _apply_free_quota(client_id: str, today: str, limit: int) -> bool:
    """Returns True if translate is allowed (quota incremented for free tier)."""
    backend = quota_backend_name()
    if backend == "firestore":
        return await asyncio.to_thread(fs_try_increment, client_id, today, limit)
    allowed, _after = _sqlite_store().try_consume_one(client_id, today, limit)
    return allowed


def utc_day_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _valid_uuid(s: str) -> bool:
    try:
        uuid.UUID(str(s))
        return True
    except Exception:
        return False


async def translate_quota_gate(body_json: dict[str, Any], raw_body: bytes, content_type: str) -> Optional[JSONResponse]:
    """
    Returns a JSONResponse to short-circuit (429/400), or None to proceed to upstream translate.
    """
    client_id = str(body_json.get("client_id") or "").strip()
    if not client_id or not _valid_uuid(client_id):
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "reason": "missing_or_invalid_client_id",
                "reasonCode": "BAD_CLIENT_ID",
            },
        )

    customer_id = str(body_json.get("customer_id") or "").strip()
    if customer_id and await customer_is_unlimited(customer_id):
        return None

    allowed = await _apply_free_quota(client_id, utc_day_iso(), FREE_DAILY)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "FREE_LIMIT_REACHED"},
        )
    return None


ALLOWED_ORIGINS = [
    "https://nextbase-one-ha.github.io",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "null",
]
if os.getenv("ALLOWED_ORIGINS"):
    ALLOWED_ORIGINS.extend([x.strip() for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip()])

app = FastAPI(title="smile-friend-engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
async def health():
    qb = quota_backend_name()
    return {
        "ok": True,
        "service": "smile-friend-engine",
        "quota_backend": qb,
        "quota_sqlite_path": DB_PATH if qb == "sqlite" else None,
        "free_daily": FREE_DAILY,
        "translate_mode": (
            "callable"
            if (os.getenv("GLB_TRANSLATE_CALLABLE") or "").strip()
            else ("upstream" if (os.getenv("TRANSLATE_UPSTREAM_URL") or "").strip() else "unset")
        ),
    }


@app.post("/translate")
async def translate(request: Request):
    raw = await request.body()
    ct = request.headers.get("content-type", "application/json")
    try:
        body_json = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(400, "invalid json")

    gate = await translate_quota_gate(body_json, raw, ct or "application/json")
    if gate is not None:
        return gate
    return await dispatch_translate(raw, ct or "application/json", body_json)
