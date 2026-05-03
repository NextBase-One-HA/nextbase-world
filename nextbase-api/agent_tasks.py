"""
Agent task evidence tracking.

Purpose: kill AI "done without evidence" behavior.
DONE is only allowed when physical evidence exists:
- git_commit
- deploy_revision
- test_command
- test_response

Open-task listing is injected into POST /gateway under ### OPEN_AGENT_TASKS ###.
DONE-rule violations are written to agent_violations.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from google.cloud import firestore

_fs: firestore.Client | None = None
COL_AGENT_TASKS = "agent_tasks"
COL_AGENT_VIOLATIONS = "agent_violations"
COL_AGENT_REPUTATION = "agent_reputation"
DEFAULT_TTL_HOURS = int(os.getenv("NEXTBASE_AGENT_TASK_TTL_HOURS", "12"))
REQUIRED_EVIDENCE = ("git_commit", "deploy_revision", "test_command", "test_response")
DONE_CLAIM_MARKERS = (
    '"status":"DONE"',
    '"status": "DONE"',
    "status=DONE",
    "Evidence verified",
    "Deployment confirmed",
    "完了しました",
    "完了です",
    "完遂しました",
    "実行完了",
    "完成しました",
)
DONE_NEGATION_MARKERS = (
    "完了ではありません",
    "完了していません",
    "未完了",
    "DONEではありません",
    "not done",
    "not completed",
    "incomplete",
)


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


def _response_text(response: Any) -> str:
    if isinstance(response, dict):
        for key in ("translatedText", "text", "response", "message"):
            if response.get(key):
                return _safe_text(response.get(key))
        return _safe_text(json.dumps(response, ensure_ascii=False))
    return _safe_text(response)


def _contains_done_claim(text: str) -> bool:
    normalized = text.strip()
    lowered = normalized.lower()
    if any(marker.lower() in lowered for marker in DONE_NEGATION_MARKERS):
        return False
    return any(marker.lower() in lowered for marker in DONE_CLAIM_MARKERS)


def _blocking_tasks(open_tasks_payload: Any) -> list[dict[str, Any]]:
    tasks = []
    if isinstance(open_tasks_payload, dict):
        tasks = open_tasks_payload.get("tasks") or []
    elif isinstance(open_tasks_payload, list):
        tasks = open_tasks_payload

    blocking: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = task.get("status")
        missing = task.get("missing_evidence") or []
        if status in ("RUNNING", "HOLD") or missing:
            blocking.append(
                {
                    "task_id": task.get("task_id"),
                    "status": status,
                    "missing_evidence": missing,
                    "title": task.get("title"),
                }
            )
    return blocking


def _reputation_from_count(count: int) -> dict[str, Any]:
    score = max(0, 100 - (count * 20))
    if count >= 5:
        route_class = "blocked"
        security_level = 2
    elif count >= 3:
        route_class = "restricted"
        security_level = 1
    else:
        route_class = "normal"
        security_level = 1
    return {"score": score, "route_class": route_class, "securityLevel": security_level}


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


async def task_finish(*, task_id: str | None, evidence: dict[str, Any]) -> dict[str, Any]:
    if not task_id:
        return {"status": "HOLD", "reason": "missing_task_id", "task_id": ""}
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


async def open_tasks(limit: int = 10) -> dict[str, Any]:
    fs = _client()

    def read() -> list[dict[str, Any]]:
        query = fs.collection(COL_AGENT_TASKS).where(
            "status",
            "in",
            ["RUNNING", "HOLD"],
        ).limit(limit)
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

    rows = await asyncio.to_thread(read)
    return {"tasks": rows}


async def session_violation_count(*, session_id: str | None, limit: int = 50) -> int:
    if not session_id:
        return 0
    fs = _client()

    def read() -> int:
        query = fs.collection(COL_AGENT_VIOLATIONS).where("session_id", "==", session_id).limit(limit)
        return sum(1 for _ in query.stream())

    return await asyncio.to_thread(read)


async def reputation_status(*, session_id: str | None) -> dict[str, Any]:
    count = await session_violation_count(session_id=session_id)
    rep = _reputation_from_count(count)
    return {"session_id": session_id, "violation_count": count, **rep}


async def log_done_violation_if_needed(*, response: Any, open_tasks_payload: Any, session_id: str | None = None) -> dict[str, Any]:
    """Log if an AI response claims DONE while open tasks still lack evidence."""
    text = _response_text(response)
    if not _contains_done_claim(text):
        return {"violation_logged": False, "reason": "no_done_claim"}

    blocking = _blocking_tasks(open_tasks_payload)
    if not blocking:
        return {"violation_logged": False, "reason": "no_open_blocking_tasks"}

    prior_count = await session_violation_count(session_id=session_id)
    violation_count = prior_count + 1
    rep = _reputation_from_count(violation_count)
    severity = "critical" if violation_count >= 3 else "high"

    fs = _client()
    violation = {
        "event": "done_claim_without_evidence",
        "severity": severity,
        "session_id": session_id,
        "violation_count": violation_count,
        "reputation": rep,
        "blocking_tasks": blocking,
        "response_excerpt": _safe_text(text, 2000),
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    def write() -> str:
        ref = fs.collection(COL_AGENT_VIOLATIONS).document()
        ref.set(violation)
        if session_id:
            fs.collection(COL_AGENT_REPUTATION).document(session_id).set(
                {
                    "session_id": session_id,
                    "violation_count": violation_count,
                    **rep,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )
        return ref.id

    violation_id = await asyncio.to_thread(write)
    return {
        "violation_logged": True,
        "violation_id": violation_id,
        "reason": "done_claim_without_evidence",
        "severity": severity,
        "violation_count": violation_count,
        **rep,
    }
