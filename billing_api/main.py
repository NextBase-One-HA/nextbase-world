"""
NextBase / Smile-Friend billing: Stripe Customer Portal + webhooks + entitlements (SQLite).
Deploy to Cloud Run; set STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, TRANSLATE_PROXY_URL (optional).
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

import httpx
import stripe
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
PORTAL_RETURN_URL = os.getenv(
    "PORTAL_RETURN_URL",
    "https://nextbase-one-ha.github.io/nextbase-world/index.coreflow.html",
)
TRANSLATE_PROXY_URL = os.getenv("TRANSLATE_PROXY_URL", "").rstrip("/")

DB_PATH = os.getenv("BILLING_DB_PATH", str(Path(__file__).resolve().parent / "billing_entitlements.db"))
GRACE_SECONDS = int(os.getenv("PAYMENT_FAILED_GRACE_SECONDS", str(72 * 3600)))

# Comma-separated price ids; empty = any active/trialing/past_due(within grace) subscription counts as core
STRIPE_CORE_PRICE_IDS = {
    x.strip()
    for x in os.getenv("STRIPE_CORE_PRICE_IDS", "").split(",")
    if x.strip()
}
STRIPE_TRAVEL_PRICE_IDS = {
    x.strip()
    for x in os.getenv("STRIPE_TRAVEL_PRICE_IDS", "").split(",")
    if x.strip()
}

stripe.api_key = STRIPE_SECRET_KEY

ALLOWED_ORIGINS = [
    "https://nextbase-one-ha.github.io",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "null",
]
if os.getenv("ALLOWED_ORIGINS"):
    ALLOWED_ORIGINS.extend(os.getenv("ALLOWED_ORIGINS", "").split(","))

app = FastAPI(title="NextBase Billing", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Stripe-Signature"],
)


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    c = _conn()
    try:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_entitlements (
                stripe_customer_id TEXT PRIMARY KEY,
                core_subscribed INTEGER NOT NULL DEFAULT 0,
                travel_active INTEGER NOT NULL DEFAULT 0,
                subscription_status TEXT,
                payment_failed INTEGER NOT NULL DEFAULT 0,
                payment_failed_at REAL,
                grace_until REAL,
                updated_at REAL NOT NULL
            )
            """
        )
        c.commit()
    finally:
        c.close()


init_db()


def _upsert_row(
    customer_id: str,
    core: int,
    travel: int,
    sub_status: Optional[str],
    payment_failed: int,
    failed_at: Optional[float],
    grace_until: Optional[float],
) -> None:
    now = time.time()
    c = _conn()
    try:
        c.execute(
            """
            INSERT INTO customer_entitlements (
                stripe_customer_id, core_subscribed, travel_active, subscription_status,
                payment_failed, payment_failed_at, grace_until, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stripe_customer_id) DO UPDATE SET
                core_subscribed = excluded.core_subscribed,
                travel_active = excluded.travel_active,
                subscription_status = excluded.subscription_status,
                payment_failed = excluded.payment_failed,
                payment_failed_at = excluded.payment_failed_at,
                grace_until = excluded.grace_until,
                updated_at = excluded.updated_at
            """,
            (
                customer_id,
                core,
                travel,
                sub_status or "",
                payment_failed,
                failed_at,
                grace_until,
                now,
            ),
        )
        c.commit()
    finally:
        c.close()


def _row(customer_id: str) -> Optional[sqlite3.Row]:
    c = _conn()
    try:
        cur = c.execute(
            "SELECT * FROM customer_entitlements WHERE stripe_customer_id = ?",
            (customer_id,),
        )
        return cur.fetchone()
    finally:
        c.close()


def _price_ids_from_subscription(sub: Any) -> set[str]:
    out: set[str] = set()
    items = getattr(sub, "items", None) or sub.get("items") if isinstance(sub, dict) else None
    if not items:
        return out
    data = getattr(items, "data", None) or items.get("data", [])
    for it in data or []:
        price = it.get("price") if isinstance(it, dict) else getattr(it, "price", None)
        if not price:
            continue
        pid = price.get("id") if isinstance(price, dict) else getattr(price, "id", None)
        if pid:
            out.add(str(pid))
    return out


def _subscription_matches_core(price_ids: set[str]) -> bool:
    if not STRIPE_CORE_PRICE_IDS:
        return True
    return bool(price_ids & STRIPE_CORE_PRICE_IDS)


def _subscription_matches_travel(price_ids: set[str]) -> bool:
    if not STRIPE_TRAVEL_PRICE_IDS:
        return False
    return bool(price_ids & STRIPE_TRAVEL_PRICE_IDS)


def recompute_customer(customer_id: str) -> None:
    """Recompute core/travel from all Stripe subscriptions for customer."""
    if not STRIPE_SECRET_KEY or not customer_id.startswith("cus_"):
        return
    now = time.time()
    row = _row(customer_id)
    grace_until = float(row["grace_until"] or 0) if row else 0.0

    subs = stripe.Subscription.list(customer=customer_id, status="all", limit=30)
    core_any = 0
    travel_any = 0
    status_last = ""
    past_due_core = 0

    for s in subs.auto_paging_iter():
        st = getattr(s, "status", "") or ""
        status_last = st or status_last
        pids = _price_ids_from_subscription(s)
        cm = _subscription_matches_core(pids)
        tm = _subscription_matches_travel(pids)
        if st in ("active", "trialing"):
            if cm:
                core_any = 1
            if tm:
                travel_any = 1
        elif st == "past_due" and cm:
            past_due_core = 1

    if past_due_core:
        if grace_until > now:
            core_any = 1
        else:
            core_any = 0

    pay_fail = 1 if (past_due_core and grace_until > now) else (1 if past_due_core else 0)
    failed_at = row["payment_failed_at"] if row else None
    g_keep = grace_until if past_due_core else None

    _upsert_row(
        customer_id,
        core_any,
        travel_any,
        status_last,
        pay_fail,
        failed_at,
        g_keep,
    )


def sync_from_stripe_customer(customer_id: str) -> None:
    recompute_customer(customer_id)


def compute_entitlement_response(customer_id: str) -> dict[str, Any]:
    row = _row(customer_id)
    if not row:
        return {"ok": True, "customer_id": customer_id, "core_subscribed": False, "travel_active": False}

    core = bool(row["core_subscribed"])
    travel = bool(row["travel_active"])
    st = (row["subscription_status"] or "").strip()
    grace = float(row["grace_until"] or 0)
    failed = int(row["payment_failed"] or 0)

    now = time.time()
    if st == "past_due" and failed and grace > now:
        core = True
    if st in ("canceled", "unpaid", "incomplete_expired"):
        core = False
        travel = False

    return {
        "ok": True,
        "customer_id": customer_id,
        "core_subscribed": core,
        "travel_active": travel,
        "subscription_status": st or None,
        "billing_grace": bool(st == "past_due" and grace > now),
    }


class PortalBody(BaseModel):
    customer_id: str


@app.post("/billing/portal")
async def billing_portal(body: PortalBody):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "STRIPE_SECRET_KEY not configured")
    cid = (body.customer_id or "").strip()
    if not cid.startswith("cus_"):
        raise HTTPException(400, "invalid customer_id")
    try:
        sess = stripe.billing_portal.Session.create(
            customer=cid,
            return_url=PORTAL_RETURN_URL,
        )
        return {"url": sess.url}
    except Exception as e:
        raise HTTPException(502, str(e)) from e


@app.post("/create-portal-session")
async def create_portal_session_alias(body: PortalBody):
    return await billing_portal(body)


@app.get("/entitlements")
async def entitlements(customer_id: Optional[str] = None, session_id: Optional[str] = None):
    if not STRIPE_SECRET_KEY:
        return JSONResponse(
            {
                "ok": False,
                "reason": "stripe_not_configured",
                "core_subscribed": False,
                "travel_active": False,
            }
        )
    cid = (customer_id or "").strip()
    sid = (session_id or "").strip()

    if sid.startswith("cs_"):
        try:
            checkout = stripe.checkout.Session.retrieve(sid, expand=["subscription"])
            c = getattr(checkout, "customer", None)
            if c:
                cid = str(c)
                recompute_customer(cid)
        except Exception:
            pass

    if not cid or not cid.startswith("cus_"):
        return {"ok": False, "reason": "missing_customer", "core_subscribed": False, "travel_active": False}

    try:
        sync_from_stripe_customer(cid)
    except Exception:
        pass

    data = compute_entitlement_response(cid)
    return data


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature") or ""

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        except ValueError as e:
            raise HTTPException(400, f"invalid payload: {e}") from e
        except Exception as e:
            raise HTTPException(400, f"invalid signature: {e}") from e
    else:
        try:
            event = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise HTTPException(400, str(e)) from e

    et = event.get("type") if isinstance(event, dict) else getattr(event, "type", "")
    data = event.get("data", {}) if isinstance(event, dict) else getattr(event, "data", {})
    obj = data.get("object", {}) if isinstance(data, dict) else {}

    if et == "customer.subscription.updated":
        cid = obj.get("customer") if isinstance(obj, dict) else getattr(obj, "customer", None)
        if cid:
            recompute_customer(str(cid))
    elif et == "customer.subscription.deleted":
        cid = obj.get("customer")
        if cid:
            recompute_customer(str(cid))
    elif et == "invoice.payment_succeeded":
        customer = obj.get("customer")
        if customer:
            sync_from_stripe_customer(str(customer))
    elif et == "invoice.payment_failed":
        customer = obj.get("customer")
        if customer:
            cid = str(customer)
            r = _row(cid)
            _upsert_row(
                cid,
                int(r["core_subscribed"]) if r else 1,
                int(r["travel_active"]) if r else 0,
                "past_due",
                1,
                time.time(),
                time.time() + GRACE_SECONDS,
            )
            recompute_customer(cid)
    elif et in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        session = obj
        cid = session.get("customer") if isinstance(session, dict) else getattr(session, "customer", None)
        if cid:
            recompute_customer(str(cid))

    return {"received": True, "type": et}


@app.post("/translate")
async def translate_proxy(request: Request):
    if not TRANSLATE_PROXY_URL:
        raise HTTPException(
            501,
            "TRANSLATE_PROXY_URL not set; configure upstream or deploy merged translate",
        )
    body = await request.body()
    ct = request.headers.get("content-type", "application/json")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{TRANSLATE_PROXY_URL}/translate",
                content=body,
                headers={"Content-Type": ct},
            )
        return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))
    except Exception as e:
        raise HTTPException(502, str(e)) from e


@app.get("/health")
async def health():
    return {"ok": True, "billing_db": DB_PATH}

