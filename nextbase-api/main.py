"""
NextBase API:
- POST /gateway — canonical + inventory + optional session + OPEN_AGENT_TASKS, then TRANSLATE_UPSTREAM_URL.
- POST /agent/task/* — agent task ledger (Firestore agent_tasks).
- POST /rooms/* — Firestore rooms / messages / audit_logs.

Canonical: NEXTBASE_CANONICAL_URL or local NEXTBASE_SYSTEM_CANONICAL.md.
Inventory: NEXTBASE_INVENTORY_URL or local SYSTEM_INVENTORY.md.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import agent_tasks
import httpx
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

import rooms_firestore
import session_firestore

CANONICAL_FETCH_TIMEOUT = float(os.getenv("NEXTBASE_CANONICAL_FETCH_TIMEOUT", "15"))


def _docs_base_dir() -> Path:
    here = Path(__file__).resolve().parent
    monorepo_docs = here.parent / "docs"
    local_docs = here / "docs"
    if (monorepo_docs / "NEXTBASE_SYSTEM_CANONICAL.md").is_file():
        return monorepo_docs
    if (local_docs / "NEXTBASE_SYSTEM_CANONICAL.md").is_file():
        return local_docs
    return monorepo_docs


def _path_canonical_local() -> Path:
    return _docs_base_dir() / "NEXTBASE_SYSTEM_CANONICAL.md"


def _path_inventory_local() -> Path:
    return _docs_base_dir() / "SYSTEM_INVENTORY.md"


async def canonical_loader() -> tuple[str | None, str | None]:
    url = (os.getenv("NEXTBASE_CANONICAL_URL") or "").strip()
    if url:
        try:
            async with httpx.AsyncClient(timeout=CANONICAL_FETCH_TIMEOUT) as client:
                r = await client.get(url)
            if r.status_code == 200:
                return r.text, None
        except Exception:
            pass

    local = _path_canonical_local()
    if local.is_file():
        return local.read_text(encoding="utf-8"), None
    return None, "canonical_load_failed"


async def inventory_loader() -> tuple[str | None, str | None]:
    url = (os.getenv("NEXTBASE_INVENTORY_URL") or "").strip()
    if url:
        try:
            async with httpx.AsyncClient(timeout=CANONICAL_FETCH_TIMEOUT) as client:
                r = await client.get(url)
            if r.status_code == 200:
                return r.text, None
        except Exception:
            pass

    p = _path_inventory_local()
    if p.is_file():
        return p.read_text(encoding="utf-8"), None
    return None, "inventory_load_failed"


def security_level_hold(combined_audit_text: str) -> bool:
    if "STATE: HOLD" in combined_audit_text:
        return True
    if "STATE: INVALID" in combined_audit_text:
        return True
    return False


def _hold(*, reason: str) -> dict:
    out: dict = {"status": "HOLD", "securityLevel": 1}
    if reason:
        out["reason"] = reason
    return out


app = FastAPI(
    title="NextBase API — Gateway + Rooms + Sessions + Agent Tasks",
    version="1.3.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GatewayPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt: str = ""
    target: str = ""
    caller_id: str = "prod"
    model: str | None = None
    session_id: str | None = None


async def forward_to_ai_router(enforced_prompt: str, payload: GatewayPayload) -> dict:
    base = (os.getenv("TRANSLATE_UPSTREAM_URL") or "").rstrip("/")
    if not base:
        raise HTTPException(status_code=500, detail="TRANSLATE_UPSTREAM_URL is not set")
    body = payload.model_dump(exclude_none=True)
    body.pop("prompt", None)
    body["text"] = enforced_prompt

    url = f"{base}/gateway"
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, json=body)
    try:
        data = r.json()
    except Exception:
        data = {"upstream_status": r.status_code}
    if r.is_success:
        return data
    raise HTTPException(status_code=r.status_code, detail=data)


@app.post("/gateway")
async def mandatory_gateway(payload: GatewayPayload):
    canonical_text, c_err = await canonical_loader()
    if c_err or not canonical_text:
        return _hold(reason=c_err or "canonical_error")

    inventory_text, i_err = await inventory_loader()
    if i_err or not inventory_text:
        return _hold(reason=i_err or "inventory_error")

    audit_blob = canonical_text + "\n\n---\n\n" + inventory_text
    if security_level_hold(audit_blob):
        return _hold(reason="inventory_state_hold_or_invalid")

    session_context = ""
    if payload.session_id:
        session_context = await session_firestore.session_context(
            session_id=payload.session_id,
            canonical_snapshot=canonical_text,
            inventory_snapshot=inventory_text,
        )

    try:
        open_tasks_payload = await agent_tasks.open_tasks()
        if isinstance(open_tasks_payload, list):
            open_tasks_payload = {"tasks": open_tasks_payload}
        open_tasks_text = json.dumps(open_tasks_payload, ensure_ascii=False, indent=2)
    except Exception:
        open_tasks_text = json.dumps(
            {"tasks": [], "error": "open_tasks_unavailable"}, ensure_ascii=False
        )

    blocks = [
        f"### SYSTEM_CANONICAL_LAW ###\n{canonical_text}\n\n",
        f"### SYSTEM_INVENTORY ###\n{inventory_text}\n\n",
    ]
    if session_context:
        blocks.append(f"### SESSION_CONTEXT ###\n{session_context}\n\n")
    blocks.append(f"### OPEN_AGENT_TASKS ###\n{open_tasks_text}\n\n")
    blocks.append(f"### USER_REQUEST ###\n{payload.prompt}")
    enforced_prompt = "".join(blocks)

    result = await forward_to_ai_router(enforced_prompt, payload)

    if payload.session_id:
        await session_firestore.session_record_exchange(
            session_id=payload.session_id,
            user_prompt=payload.prompt,
            assistant_response=result,
        )

    return result


@app.get("/health")
def health():
    return {"status": "ok", "protocol": "NEXTBASE_API_GATEWAY_FIXED"}


@app.post("/agent/task/start")
async def agent_task_start(body: dict = Body(...)):
    return await agent_tasks.task_start(
        title=body.get("title", "untitled"),
        detail=body.get("detail", {}),
        ttl_hours=body.get("ttl_hours"),
    )


@app.post("/agent/task/finish")
async def agent_task_finish(body: dict = Body(...)):
    task_id = body.get("task_id")
    if not task_id:
        return {"status": "HOLD", "securityLevel": 1, "reason": "missing_task_id"}
    return await agent_tasks.task_finish(
        task_id=task_id,
        evidence=body.get("evidence", {}),
    )


@app.get("/agent/task/{task_id}")
async def agent_task_get(task_id: str):
    return await agent_tasks.task_get(task_id=task_id)


@app.get("/agent/tasks/open")
async def agent_tasks_open():
    return await agent_tasks.open_tasks()


# --- Firestore: rooms / TTL / messages / audit (no Stripe / no billing lock) ---


class RoomCreateBody(BaseModel):
    ttl_days: int = Field(default=30, ge=1, le=365)


class RoomJoinBody(BaseModel):
    code: str


class RoomMessageBody(BaseModel):
    code: str
    body: str
    sender_id: str | None = None


class RoomStatusBody(BaseModel):
    code: str


@app.post("/rooms/create")
async def rooms_create(body: RoomCreateBody):
    try:
        return await rooms_firestore.room_create(ttl_days=body.ttl_days)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="room_code_collision")


@app.post("/rooms/join")
async def rooms_join(body: RoomJoinBody):
    out = await rooms_firestore.room_join(code=body.code)
    if out.get("ok"):
        return out
    err = out.get("error", "unknown")
    if err == "not_found":
        raise HTTPException(status_code=404, detail=err)
    if err == "expired":
        raise HTTPException(status_code=410, detail=err)
    raise HTTPException(status_code=400, detail=err)


@app.post("/rooms/message")
async def rooms_message(body: RoomMessageBody):
    out = await rooms_firestore.room_message(
        room_code=body.code,
        body=body.body,
        sender_id=body.sender_id,
    )
    if out.get("ok"):
        return out
    err = out.get("error", "unknown")
    if err == "not_found":
        raise HTTPException(status_code=404, detail=err)
    if err == "expired":
        raise HTTPException(status_code=410, detail=err)
    raise HTTPException(status_code=400, detail=err)


@app.post("/rooms/status")
async def rooms_status_post(body: RoomStatusBody):
    return await rooms_firestore.room_status(code=body.code)


@app.get("/rooms/status")
async def rooms_status_get(code: str = Query(..., min_length=1)):
    return await rooms_firestore.room_status(code=code)


@app.get("/sessions/status")
async def sessions_status(session_id: str = Query(...)):
    return await session_firestore.session_status(session_id=session_id)
