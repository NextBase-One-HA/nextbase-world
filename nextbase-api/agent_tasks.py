"""
Agent task evidence tracking.

Purpose: kill AI "done without evidence" behavior.
DONE is only allowed when physical evidence exists:
- git_commit
- deploy_revision
- test_command
- test_response
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from google.cloud import firestore

_fs: firestore.Client | None = None
COL_AGENT_TASKS = "agent_tasks"
DEFAULT_TTL_HOURS = int(os.getenv("NEXTBASE_AGENT_TASK_TTL_HOURS", "12"))
REQUIRED_EVIDENCE = ("git_commit", "deploy_revision", "test_command", "test_response")


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


def _safe_text(value: Any, limit: int = 12000) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def _missing_evidence(evidence: dict[str, Any]) -> list[str]:
    return [key for key in REQUIRED_EVIDENCE if not evidence.get(key)]


def _status_from_evidence(evidence: dict[str, Any]) -> tuple[str, list[str]]:
    missing = _missing_evidence(evidence)
    if missing:
        return "HOLD", missing
    return "DONE", []


async def task_start(*, title: str, detail: dict[str, Any] | None = None, ttl_hours: int | None = None) -> dict[str, Any]:
    fs = _client()
    task_id = uuid4().hex[:16]
    ttl = int(ttl_hours or DEFAULT_TTL_HOURS)
    started_at = _now()
    expires_at = started_at + timedelta(hours=ttl)
    ref = fs.collection(COL_AGENT_TASKS).document(task_id)

    payload = {
        "task_id": task_id,
        "title": title,
        "detail": detail or {},
        "status": "RUNNING",
        "evidence": {},
        "missing_evidence": list(REQUIRED_EVIDENCE),
        "hold_timer": {
            "start_time": started_at.isoformat(),
            "ttl_hours": ttl,
            "expires_at": expires_at.isoformat(),
        },
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    def write() -> None:
        ref.set(payload)

    await asyncio.to_thread(write)
    return {
        "status": "RUNNING",
        "task_id": task_id,
        "required_evidence": list(REQUIRED_EVIDENCE),
        "expires_at": expires_at.isoformat(),
    }


async def task_finish(*, task_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    fs = _client()
    ref = fs.collection(COL_AGENT_TASKS).document(task_id)

    def update() -> dict[str, Any]:
        snap = ref.get()
        if not snap.exists:
            return {"status": "HOLD", "reason": "task_not_found", "task_id": task_id}
        existing = snap.to_dict() or {}
        merged = dict(existing.get("evidence") or {})
        for key, value in evidence.items():
            merged[key] = _safe_text(value)
        status, missing = _status_from_evidence(merged)
        payload = {
            "status": status,
            "evidence": merged,
            "missing_evidence": missing,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        if status == "DONE":
            payload["done_at"] = firestore.SERVER_TIMESTAMP
        ref.set(payload, merge=True)
        if status == "DONE":
            return {
                "status": "DONE",
                "task_id": task_id,
                "message": "Evidence verified. Deployment confirmed.",
            }
        return {
            "status": "HOLD",
            "securityLevel": 1,
            "task_id": task_id,
            "reason": "missing_evidence",
            "missing_evidence": missing,
        }

    return await asyncio.to_thread(update)


async def task_get(*, task_id: str) -> dict[str, Any]:
    fs = _client()
    ref = fs.collection(COL_AGENT_TASKS).document(task_id)

    def read() -> dict[str, Any]:
        snap = ref.get()
        if not snap.exists:
            return {"exists": False, "task_id": task_id, "status": "HOLD", "reason": "task_not_found"}
        data = snap.to_dict() or {}
        evidence = data.get("evidence") or {}
        status, missing = _status_from_evidence(evidence)
        # If task was still RUNNING but all evidence now exists, report DONE shape too.
        return {
            "exists": True,
            "task_id": task_id,
            "status": data.get("status") or status,
            "missing_evidence": data.get("missing_evidence") or missing,
            "evidence": evidence,
            "hold_timer": data.get("hold_timer") or {},
            "title": data.get("title"),
        }

    return await asyncio.to_thread(read)


async def open_tasks(limit: int = 10) -> list[dict[str, Any]]:
    fs = _client()

    def read() -> list[dict[str, Any]]:
        query = (
            fs.collection(COL_AGENT_TASKS)
            .where(filter=firestore.FieldFilter("status", "in", ["RUNNING", "HOLD"]))
            .limit(limit)
        )
        out: list[dict[str, Any]] = []
        for snap in query.stream():
            data = snap.to_dict() or {}
            out.append(
                {
                    "task_id": data.get("task_id") or snap.id,
                    "status": data.get("status"),
                    "title": data.get("title"),
                    "missing_evidence": data.get("missing_evidence") or [],
                    "hold_timer": data.get("hold_timer") or {},
                }
            )
        return out

    return await asyncio.to_thread(read)
