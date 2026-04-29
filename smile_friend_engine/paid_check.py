"""Resolve paid / unlimited translate via billing entitlements API."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import httpx


def _entitlements_url(customer_id: str) -> str:
    base = (os.getenv("BILLING_ENTITLEMENTS_BASE") or "").rstrip("/")
    return f"{base}/entitlements?customer_id={quote(customer_id, safe='')}"


async def customer_is_unlimited(customer_id: str) -> bool:
    """
    True if core_subscribed or travel_active for this Stripe customer.
    If billing base URL is not configured, returns False.
    On HTTP error, returns False (quota still applies).
    """
    cid = (customer_id or "").strip()
    if not cid.startswith("cus_"):
        return False
    if not (os.getenv("BILLING_ENTITLEMENTS_BASE") or "").strip():
        return False
    url = _entitlements_url(cid)
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(url)
        if r.status_code != 200:
            return False
        data: dict[str, Any] = r.json()
        return bool(data.get("core_subscribed") or data.get("travel_active"))
    except Exception:
        return False


def customer_is_unlimited_sync(customer_id: str) -> bool:
    """Sync variant for tests."""
    cid = (customer_id or "").strip()
    if not cid.startswith("cus_"):
        return False
    if not (os.getenv("BILLING_ENTITLEMENTS_BASE") or "").strip():
        return False
    url = _entitlements_url(cid)
    try:
        with httpx.Client(timeout=12.0) as client:
            r = client.get(url)
        if r.status_code != 200:
            return False
        data = r.json()
        return bool(data.get("core_subscribed") or data.get("travel_active"))
    except Exception:
        return False
