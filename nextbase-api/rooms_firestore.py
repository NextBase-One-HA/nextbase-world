"""
Rooms / messages / audit_logs — Firestore is the only source of truth for TTL and room state.
No state is stored on ai-router.
"""
from __future__ import annotations

import asyncio
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from google.cloud import firestore

_fs: firestore.Client | None = None

COL_ROOMS = "rooms"
COL_MESSAGES = "messages"
COL_AUDIT = "audit_logs"
MAX_MESSAGE_CHARS = int(os.getenv("GLB_ROOM_MESSAGE_MAX_CHARS", "2000"))


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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def normalize_room_code(raw: str) -> str:
    digits = "".join(c for c in (raw or "") if c.isdigit())
    if not digits:
        return ""
    if len(digits) >= 6:
        return digits[:6]
    return digits.zfill(6)


def _gen_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _expires_valid(expires_at: Any) -> bool:
    ex = _as_utc(expires_at)
    return bool(ex and ex > _utc_now())


def _validate_message_body(body: str) -> tuple[str | None, str | None]:
    text = str(body or "").strip()
    if not text:
        return None, "empty_message"
    if len(text) > MAX_MESSAGE_CHARS:
        return None, "message_too_long"
    return text, None


async def _audit(event: str, room_id: str, detail: dict[str, Any] | None = None) -> None:
    fs = _client()

    def _write() -> None:
        fs.collection(COL_AUDIT).add(
            {
                "event": event,
                "room_id": room_id,
                "detail": detail or {},
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )

    await asyncio.to_thread(_write)


async def room_create(
    *,
    ttl_days: int = 30,
    host_customer_id: str | None = None,
    max_expires_at: Any = None,
) -> dict[str, Any]:
    fs = _client()
    requested_expires_dt = _utc_now() + timedelta(days=ttl_days)
    host_expires_dt = _as_utc(max_expires_at)
    expires_dt = min(requested_expires_dt, host_expires_dt) if host_expires_dt else requested_expires_dt

    if expires_dt <= _utc_now():
        return {"ok": False, "error": "travel_pass_expired"}

    for _ in range(24):
        code = _gen_code()
        ref = fs.collection(COL_ROOMS).document(code)

        def try_create(
            r: Any = ref,
            c: str = code,
            exp: datetime = expires_dt,
            td: int = ttl_days,
            host: str | None = host_customer_id,
        ) -> bool:
            snap = r.get()
            if snap.exists:
                return False
            r.set(
                {
                    "code": c,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "expires_at": exp,
                    "ttl_days": td,
                    "host_customer_id": host,
                    "room_type": "travel",
                }
            )
            return True

        ok = await asyncio.to_thread(try_create)
        if not ok:
            continue

        await _audit("room_created", code, {"ttl_days": ttl_days, "host_customer_id": host_customer_id})
        return {
            "ok": True,
            "room_id": code,
            "code": code,
            "expires_at": expires_dt.isoformat(),
            "ttl_days": ttl_days,
        }

    raise RuntimeError("room_code_collision")


async def room_get_snapshot(code: str) -> tuple[dict[str, Any] | None, str | None]:
    norm = normalize_room_code(code)
    if len(norm) != 6:
        return None, "invalid_code"
    fs = _client()
    ref = fs.collection(COL_ROOMS).document(norm)

    def read() -> Any:
        return ref.get()

    snap = await asyncio.to_thread(read)
    if not snap.exists:
        return None, "not_found"
    data = snap.to_dict() or {}
    if not _expires_valid(data.get("expires_at")):
        return None, "expired"
    return data, None


async def room_join(*, code: str) -> dict[str, Any]:
    data, err = await room_get_snapshot(code)
    if err:
        return {"ok": False, "error": err}
    assert data is not None
    rid = str(data.get("code") or normalize_room_code(code))
    ex = _as_utc(data.get("expires_at"))
    ex_iso = ex.isoformat() if ex else ""
    await _audit("room_join", rid, {})
    return {"ok": True, "room_id": rid, "code": rid, "expires_at": ex_iso}


async def room_message(*, room_code: str, body: str, sender_id: str | None) -> dict[str, Any]:
    text, validation_err = _validate_message_body(body)
    if validation_err:
        return {"ok": False, "error": validation_err}

    data, err = await room_get_snapshot(room_code)
    if err:
        return {"ok": False, "error": err}
    assert data is not None and text is not None
    rid = str(data.get("code") or normalize_room_code(room_code))
    fs = _client()

    def write_msg() -> str:
        doc_ref = fs.collection(COL_MESSAGES).document()
        doc_ref.set(
            {
                "room_id": rid,
                "body": text,
                "sender_id": sender_id,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return doc_ref.id

    msg_id = await asyncio.to_thread(write_msg)
    await _audit("message_posted", rid, {"message_id": msg_id, "sender_id": sender_id})
    return {"ok": True, "room_id": rid, "message_id": msg_id}


async def room_messages(*, code: str, limit: int = 50) -> dict[str, Any]:
    data, err = await room_get_snapshot(code)
    if err:
        return {"ok": False, "error": err, "messages": []}
    assert data is not None
    rid = str(data.get("code") or normalize_room_code(code))
    safe_limit = max(1, min(int(limit or 50), 100))
    fs = _client()

    def read() -> list[dict[str, Any]]:
        query = (
            fs.collection(COL_MESSAGES)
            .where("room_id", "==", rid)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(safe_limit)
        )
        rows: list[dict[str, Any]] = []
        for snap in query.stream():
            d = snap.to_dict() or {}
            created = _as_utc(d.get("created_at"))
            rows.append(
                {
                    "message_id": snap.id,
                    "room_id": rid,
                    "body": d.get("body") or "",
                    "sender_id": d.get("sender_id"),
                    "created_at": created.isoformat() if created else None,
                }
            )
        return list(reversed(rows))

    return {"ok": True, "room_id": rid, "messages": await asyncio.to_thread(read)}


async def room_status(*, code: str) -> dict[str, Any]:
    norm = normalize_room_code(code)
    if len(norm) != 6:
        return {"exists": False, "error": "invalid_code"}
    fs = _client()
    ref = fs.collection(COL_ROOMS).document(norm)

    def read() -> Any:
        return ref.get()

    snap = await asyncio.to_thread(read)
    if not snap.exists:
        return {"exists": False, "error": "not_found"}
    data = snap.to_dict() or {}
    ex_utc = _as_utc(data.get("expires_at"))
    if not ex_utc:
        return {"exists": True, "error": "bad_schema"}
    remaining = (ex_utc - _utc_now()).total_seconds()
    expired = remaining <= 0
    return {
        "exists": True,
        "room_id": norm,
        "code": norm,
        "expires_at": ex_utc.isoformat(),
        "expired": expired,
        "seconds_remaining": max(0, int(remaining)),
        "host_customer_id": data.get("host_customer_id"),
        "room_type": data.get("room_type") or "travel",
    }
