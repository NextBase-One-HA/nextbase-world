"""GLB billing entitlement ledger.

Stripe is the payment processor. NextBase OS is the entitlement source of truth.
Firestore collections:
- entitlements/{customer_id}
- checkout_sessions/{checkout_session_id}

Core $2.99 lets a user join rooms.
Travel $14.99 lets a user create rooms for 30 days and join rooms.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import stripe
from google.cloud import firestore

_fs: firestore.Client | None = None

COL_ENTITLEMENTS = "entitlements"
COL_CHECKOUT_SESSIONS = "checkout_sessions"
CORE_PRODUCT = "core"
TRAVEL_PRODUCT = "travel"
TRAVEL_TTL_DAYS = int(os.getenv("GLB_TRAVEL_TTL_DAYS", "30"))

MESSAGE_PAYMENT_PROCESSING = "Payment is being confirmed. Please try again in a few seconds."
MESSAGE_TRAVEL_REQUIRED = "A valid 30-day Travel Pass is required to create a room."
MESSAGE_CORE_OR_TRAVEL_REQUIRED = "A valid GLB Core subscription or Travel Pass is required to join this room."
MESSAGE_CHECKOUT_NOT_CONFIGURED = "Checkout is temporarily unavailable. Please contact support."


def _client() -> firestore.Client:
    global _fs
    if _fs is None:
        project = (
            os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT")
            or os.getenv("GCLOUD_PROJECT")
            or None
        )
        _fs = firestore.Client(project=project) if project else firestore.Client()
    return _fs


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(value)


def _is_active_until(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt > _now()
    return True


def _normalize_customer_id(customer_id: str | None) -> str:
    return str(customer_id or "").strip()


def _normalize_session_id(session_id: str | None) -> str:
    return str(session_id or "").strip()


def _product_from_session(session: dict[str, Any]) -> str | None:
    metadata = session.get("metadata") or {}
    product = (metadata.get("product") or metadata.get("glb_product") or metadata.get("plan") or "").lower()
    if product in (CORE_PRODUCT, TRAVEL_PRODUCT):
        return product

    mode = (session.get("mode") or "").lower()
    if mode == "subscription":
        return CORE_PRODUCT

    success_url = str(session.get("success_url") or "").lower()
    if "travel=1" in success_url or "14.99" in success_url or "index.14.99" in success_url:
        return TRAVEL_PRODUCT
    if "index.2.99" in success_url:
        return CORE_PRODUCT
    return None


def checkout_url(product: str) -> dict[str, Any]:
    if product == CORE_PRODUCT:
        url = os.getenv("GLB_CORE_CHECKOUT_URL") or os.getenv("STRIPE_CORE_CHECKOUT_URL")
    elif product == TRAVEL_PRODUCT:
        url = os.getenv("GLB_TRAVEL_CHECKOUT_URL") or os.getenv("STRIPE_TRAVEL_CHECKOUT_URL")
    else:
        return {"ok": False, "status": "HOLD", "reason": "unknown_product", "message": MESSAGE_CHECKOUT_NOT_CONFIGURED}
    if not url:
        return {"ok": False, "status": "HOLD", "reason": "checkout_url_not_configured", "product": product, "message": MESSAGE_CHECKOUT_NOT_CONFIGURED}
    return {"ok": True, "product": product, "checkout_url": url}


async def _resolve_customer_from_session(session_id: str | None) -> str | None:
    sid = _normalize_session_id(session_id)
    if not sid:
        return None
    fs = _client()

    def read() -> str | None:
        snap = fs.collection(COL_CHECKOUT_SESSIONS).document(sid).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        return data.get("customer_id")

    return await asyncio.to_thread(read)


async def entitlement_status(*, customer_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    sid = _normalize_session_id(session_id)
    cid = _normalize_customer_id(customer_id) or await _resolve_customer_from_session(sid)
    if not cid:
        reason = "payment_processing" if sid.startswith("cs_") else "missing_customer_or_session"
        message = MESSAGE_PAYMENT_PROCESSING if reason == "payment_processing" else "Payment identity was not found. Please reopen the purchase link or contact support."
        return {
            "ok": True,
            "status": "HOLD" if reason == "payment_processing" else "DENY",
            "reason": reason,
            "message": message,
            "customer_id": None,
            "session_id": sid or None,
            "core_subscribed": False,
            "travel_active": False,
            "travel_pass_expires_at": None,
            "room_create_allowed": False,
            "room_join_allowed": False,
            "subscription_status": "unknown",
            "billing_grace": False,
        }

    fs = _client()

    def read() -> dict[str, Any]:
        snap = fs.collection(COL_ENTITLEMENTS).document(cid).get()
        data = snap.to_dict() if snap.exists else {}
        core = bool(data.get("core_subscribed"))
        expires = data.get("travel_pass_expires_at")
        travel = bool(data.get("travel_active")) and _is_active_until(expires)
        status = "ALLOW" if (core or travel) else "DENY"
        return {
            "ok": True,
            "status": status,
            "reason": None if status == "ALLOW" else "no_active_entitlement",
            "message": "Access is active." if status == "ALLOW" else "No active GLB entitlement was found for this payment identity.",
            "customer_id": cid,
            "session_id": sid or None,
            "core_subscribed": core,
            "travel_active": travel,
            "travel_pass_expires_at": _to_iso(expires),
            "room_create_allowed": travel,
            "room_join_allowed": bool(core or travel),
            "subscription_status": data.get("subscription_status") or ("active" if core else "inactive"),
            "billing_grace": bool(data.get("billing_grace")),
        }

    return await asyncio.to_thread(read)


def denial_payload(*, reason: str, message: str, entitlement: dict[str, Any], status_code: int = 403) -> dict[str, Any]:
    status = "HOLD" if reason == "payment_processing" else "DENY"
    return {
        "ok": False,
        "status": status,
        "status_code": status_code,
        "reason": reason,
        "message": message,
        "entitlement": entitlement,
    }


async def assert_room_create_allowed(*, customer_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    ent = await entitlement_status(customer_id=customer_id, session_id=session_id)
    if ent.get("room_create_allowed"):
        return {"ok": True, "status": "ALLOW", "entitlement": ent}
    if ent.get("reason") == "payment_processing":
        return denial_payload(reason="payment_processing", message=MESSAGE_PAYMENT_PROCESSING, entitlement=ent, status_code=409)
    return denial_payload(reason="travel_pass_required", message=MESSAGE_TRAVEL_REQUIRED, entitlement=ent, status_code=403)


async def assert_room_join_allowed(*, customer_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    ent = await entitlement_status(customer_id=customer_id, session_id=session_id)
    if ent.get("room_join_allowed"):
        return {"ok": True, "status": "ALLOW", "entitlement": ent}
    if ent.get("reason") == "payment_processing":
        return denial_payload(reason="payment_processing", message=MESSAGE_PAYMENT_PROCESSING, entitlement=ent, status_code=409)
    return denial_payload(reason="core_or_travel_required", message=MESSAGE_CORE_OR_TRAVEL_REQUIRED, entitlement=ent, status_code=403)


def _event_payload(raw_body: bytes, signature: str | None) -> dict[str, Any]:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET") or ""
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or ""
    if secret:
        return stripe.Webhook.construct_event(raw_body, signature or "", secret)
    import json

    return json.loads(raw_body.decode("utf-8"))


async def process_stripe_webhook(*, raw_body: bytes, signature: str | None) -> dict[str, Any]:
    event = _event_payload(raw_body, signature)
    event_type = event.get("type")
    obj = ((event.get("data") or {}).get("object") or {})
    fs = _client()

    def write() -> dict[str, Any]:
        if event_type == "checkout.session.completed":
            session = obj
            session_id = session.get("id")
            customer_id = session.get("customer") or session.get("customer_id")
            if not customer_id:
                return {"ok": False, "status": "HOLD", "reason": "missing_customer", "message": MESSAGE_PAYMENT_PROCESSING, "event": event_type}
            product = _product_from_session(session)
            ent_ref = fs.collection(COL_ENTITLEMENTS).document(customer_id)
            now = _now()
            patch: dict[str, Any] = {
                "customer_id": customer_id,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "last_checkout_session_id": session_id,
            }
            if product == CORE_PRODUCT:
                patch.update({"core_subscribed": True, "subscription_status": "active"})
            elif product == TRAVEL_PRODUCT:
                expires = now + timedelta(days=TRAVEL_TTL_DAYS)
                patch.update(
                    {
                        "travel_active": True,
                        "travel_pass_started_at": now,
                        "travel_pass_expires_at": expires,
                    }
                )
            else:
                return {"ok": False, "status": "HOLD", "reason": "unknown_product", "message": "Payment was received, but the product type could not be confirmed. Please contact support.", "event": event_type}

            ent_ref.set(patch, merge=True)
            if session_id:
                fs.collection(COL_CHECKOUT_SESSIONS).document(session_id).set(
                    {
                        "session_id": session_id,
                        "customer_id": customer_id,
                        "product": product,
                        "created_at": firestore.SERVER_TIMESTAMP,
                    },
                    merge=True,
                )
            return {"ok": True, "status": "ALLOW", "event": event_type, "customer_id": customer_id, "product": product}

        if event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
            subscription = obj
            customer_id = subscription.get("customer")
            status = subscription.get("status") or "unknown"
            active = status in ("active", "trialing")
            if customer_id:
                fs.collection(COL_ENTITLEMENTS).document(customer_id).set(
                    {
                        "customer_id": customer_id,
                        "core_subscribed": active,
                        "subscription_status": status,
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    },
                    merge=True,
                )
            return {"ok": True, "event": event_type, "customer_id": customer_id, "subscription_status": status}

        if event_type == "invoice.payment_succeeded":
            invoice = obj
            customer_id = invoice.get("customer")
            if customer_id:
                fs.collection(COL_ENTITLEMENTS).document(customer_id).set(
                    {
                        "customer_id": customer_id,
                        "core_subscribed": True,
                        "subscription_status": "active",
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    },
                    merge=True,
                )
            return {"ok": True, "event": event_type, "customer_id": customer_id}

        if event_type == "invoice.payment_failed":
            invoice = obj
            customer_id = invoice.get("customer")
            if customer_id:
                fs.collection(COL_ENTITLEMENTS).document(customer_id).set(
                    {
                        "customer_id": customer_id,
                        "subscription_status": "past_due",
                        "billing_grace": True,
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    },
                    merge=True,
                )
            return {"ok": True, "event": event_type, "customer_id": customer_id}

        return {"ok": True, "ignored": True, "event": event_type}

    return await asyncio.to_thread(write)
