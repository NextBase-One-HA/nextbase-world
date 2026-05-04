"""
NextBase / Smile-Friend billing: Stripe Customer Portal + webhooks + entitlements (SQLite).
Deploy to Cloud Run; set STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, TRANSLATE_PROXY_URL (optional).
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import hashlib
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
    "https://nextbase-one-ha.github.io/nextbase-world/index.next.html",
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


def _event_payload(raw_body: bytes, signature: str | None) -> dict[str, Any]:
    """Verify signature when configured; event body is always parsed from raw JSON."""
    secret = STRIPE_WEBHOOK_SECRET or ""
    stripe.api_key = STRIPE_SECRET_KEY or ""

    if secret:
        stripe.Webhook.construct_event(raw_body, signature or "", secret)
        return json.loads(raw_body.decode("utf-8"))

    return json.loads(raw_body.decode("utf-8"))


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


def _now_ms() -> int:
    return int(time.time() * 1000)


def hash_payload(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def append_audit_log(entry: dict[str, Any]) -> None:
    log_path = Path(__file__).resolve().parent.parent / "logs" / "audit_history.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        raise Exception(f"AUDIT_LOG_WRITE_FAILED: {e}") from e


def hold_dedup_key(entry: dict[str, Any]) -> str:
    reason = str(entry.get("reason") or "")
    route = str(entry.get("route") or "")
    canonical_hash = str(entry.get("canonical_hash") or "")
    return f"{reason}|{route}|{canonical_hash}"


def _dedup_index_path() -> Path:
    return Path(__file__).resolve().parent.parent / "logs" / "bee_dedup_index.json"


def _bee_log_path() -> Path:
    return Path(__file__).resolve().parent.parent / "logs" / "bee_fix_suggestions.jsonl"


def _load_dedup_index() -> dict[str, Any]:
    path = _dedup_index_path()
    if not path.exists():
        return {"seen": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"seen": {}}


def _save_dedup_index(index_obj: dict[str, Any]) -> None:
    path = _dedup_index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def should_generate_bee_fix(entry: dict[str, Any]) -> bool:
    if str(entry.get("result")) != "HOLD":
        return False
    key = hold_dedup_key(entry)
    index_obj = _load_dedup_index()
    seen = index_obj.get("seen", {})
    return key not in seen


def build_bee_fix_proposal(entry: dict[str, Any]) -> dict[str, Any]:
    reason = str(entry.get("reason") or "")
    route = str(entry.get("route") or "")
    if "ORE_APPROVAL_REQUIRED" in reason:
        action = "Request ORE approval header and retry guarded action."
    elif "CANONICAL_HASH_MISMATCH" in reason:
        action = "Reload canonical file, recompute canonical_hash, and retry."
    elif "GATE_A_" in reason:
        action = "Align gate_a_required_flags with NE_MODE policy and retry."
    else:
        action = "Run SELF_FIX_NOW: reload canonical, rebuild payload, retry preflight."
    return {
        "owner": "BEE",
        "route": route,
        "canonical_hash": str(entry.get("canonical_hash") or ""),
        "reason": reason,
        "proposal": action,
        "created_at": _now_ms(),
    }


def emit_bee_fix_for_hold(entry: dict[str, Any]) -> None:
    if str(entry.get("result")) != "HOLD":
        return
    key = hold_dedup_key(entry)
    index_obj = _load_dedup_index()
    seen = index_obj.get("seen", {})
    if key in seen:
        dedup_meta = dict(entry)
        dedup_meta["dedup"] = True
        dedup_meta["execution_timestamp"] = _now_ms()
        append_audit_log(dedup_meta)
        return
    proposal = build_bee_fix_proposal(entry)
    log_path = _bee_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(proposal, ensure_ascii=False) + "\n")
    seen[key] = {"created_at": _now_ms(), "owner": "BEE"}
    index_obj["seen"] = seen
    _save_dedup_index(index_obj)


def _canonical_dir() -> Path:
    """
    Law files (ORE_LAYER_*.json) live here.
    1) CANONICAL_PATH if set (directory, or a file under that tree)
    2) <this file>/canonical (container: /app/canonical)
    3) repo-root canonical for local monorepo dev: <this file>/../canonical
    """
    raw = (os.getenv("CANONICAL_PATH") or "").strip()
    if raw:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        else:
            p = p.resolve()
        if p.is_file():
            return p.parent
        return p
    here = Path(__file__).resolve().parent
    sidecar = here / "canonical"
    if sidecar.is_dir() and (sidecar / "ORE_LAYER_SYNC.json").exists():
        return sidecar
    return here.parent / "canonical"


def load_external_lock() -> dict[str, Any]:
    lock_path = _canonical_dir() / "ORE_LAYER_LOCK.json"
    with lock_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def payment_action_requires_ore_approval(lock_cfg: dict[str, Any]) -> bool:
    boundary = lock_cfg.get("approval_boundary", {})
    required = boundary.get("ore_approval_required_for", [])
    return "payment_action" in required


def ore_approval_present(request: Request) -> bool:
    token = (request.headers.get("x-ore-approval") or "").strip().lower()
    return token in {"1", "true", "yes", "approved"}


def drop_internal_state() -> dict[str, Any]:
    """Drop runtime state before each preflight reinjection."""
    return {}


def load_external_canonical() -> dict[str, Any]:
    canonical_path = _canonical_dir() / "ORE_LAYER_SYNC.json"
    with canonical_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def rebuild_payload_with_canonical(body: bytes, canonical: dict[str, Any]) -> bytes:
    data = json.loads(body.decode("utf-8"))
    data["__canonical"] = canonical
    return json.dumps(data).encode("utf-8")


def hash_canonical(canonical: dict[str, Any]) -> str:
    payload = dict(canonical)
    payload.pop("canonical_hash", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def preflight_reinject_loop(
    body: bytes,
    max_retry: int = 3,
    route: str = "/translate",
    upstream_target: str = "",
) -> tuple[bytes, dict[str, Any]]:
    last_error: Optional[str] = None
    last_result = "HOLD"
    canonical_version = ""
    canonical_hash = ""
    passcode_checked = False
    injection_timestamp = _now_ms()
    for i in range(max_retry):
        try:
            _ = drop_internal_state()
            canonical = load_external_canonical()
            if not canonical:
                raise Exception("canonical_load_failed")
            injection_timestamp = _now_ms()
            canonical_version = str(canonical.get("canonical_version") or "")
            canonical_hash = str(canonical.get("canonical_hash") or "")
            passcode_checked = bool((canonical.get("passcode") or "").strip())
            expected_hash = canonical.get("canonical_hash")
            if not expected_hash:
                raise Exception("CANONICAL_HASH_MISSING")
            actual_hash = hash_canonical(canonical)
            if actual_hash != expected_hash:
                raise Exception("CANONICAL_HASH_MISMATCH")
            gate_a_flags = (
                (canonical.get("external_correction") or {}).get("gate_a_required_flags")
            )
            if not isinstance(gate_a_flags, dict):
                raise Exception("GATE_A_FLAGS_MISSING")
            if gate_a_flags.get("mode") != "NE_MODE":
                raise Exception("GATE_A_MODE_INVALID")
            if gate_a_flags.get("human_final_authority") is not True:
                raise Exception("GATE_A_HUMAN_AUTHORITY_INVALID")
            if gate_a_flags.get("learning") is not False:
                raise Exception("GATE_A_LEARNING_INVALID")
            if gate_a_flags.get("evolution") is not False:
                raise Exception("GATE_A_EVOLUTION_INVALID")
            rebuilt = rebuild_payload_with_canonical(body, canonical)
            rebuilt_data = json.loads(rebuilt.decode("utf-8"))
            if "__canonical" not in rebuilt_data:
                raise Exception("INJECTION_FAILED")
            audit_meta = {
                "canonical_hash": canonical_hash,
                "canonical_version": canonical_version,
                "injection_timestamp": injection_timestamp,
                "payload_hash": hash_payload(rebuilt),
                "execution_timestamp": _now_ms(),
                "passcode_checked": passcode_checked,
                "reinject_retry_count": i + 1,
                "result": "PASS",
                "reason": "",
                "route": route,
                "upstream_target": upstream_target,
            }
            return rebuilt, audit_meta
        except Exception as e:  # pragma: no cover - defensive path
            last_error = str(e)
            if (
                str(e).startswith("CANONICAL_")
                or str(e).startswith("INJECTION_")
                or str(e).startswith("GATE_A_")
            ):
                last_result = "INVALID"
    failure_meta = {
        "canonical_hash": canonical_hash,
        "canonical_version": canonical_version,
        "injection_timestamp": injection_timestamp,
        "payload_hash": hash_payload(body),
        "execution_timestamp": _now_ms(),
        "passcode_checked": passcode_checked,
        "reinject_retry_count": max_retry,
        "result": last_result,
        "reason": f"REINJECT_FAILED: {last_error}",
        "route": route,
        "upstream_target": upstream_target,
    }
    append_audit_log(failure_meta)
    emit_bee_fix_for_hold(failure_meta)
    raise Exception(f"REINJECT_FAILED: {last_error}")


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


def _session_as_dict(sess: Any) -> dict[str, Any]:
    if isinstance(sess, dict):
        return sess
    try:
        td = getattr(sess, "to_dict", None)
        if callable(td):
            d = td()
            if isinstance(d, dict):
                return d
    except Exception:
        pass
    return {}


def _resolve_customer_id_from_checkout(obj: dict[str, Any]) -> Optional[str]:
    """Webhook payload often has customer=null (guest / if_required); resolve via API or email."""
    c = obj.get("customer")
    if isinstance(c, str) and c.startswith("cus_"):
        return c
    if c is not None and not isinstance(c, str):
        uid = getattr(c, "id", None) if not isinstance(c, dict) else c.get("id")
        if uid and str(uid).startswith("cus_"):
            return str(uid)

    sid = obj.get("id")
    if not isinstance(sid, str) or not sid.startswith("cs_"):
        return None
    if not STRIPE_SECRET_KEY:
        return None

    try:
        sess = stripe.checkout.Session.retrieve(sid, expand=["customer", "payment_intent"])
        sc = getattr(sess, "customer", None)
        if isinstance(sc, str) and sc.startswith("cus_"):
            return sc
        if sc is not None and not isinstance(sc, str):
            suid = getattr(sc, "id", None)
            if suid and str(suid).startswith("cus_"):
                return str(suid)
        pi = getattr(sess, "payment_intent", None)
        if pi is not None and not isinstance(pi, str):
            pc = getattr(pi, "customer", None)
            if pc and str(pc).startswith("cus_"):
                return str(pc)
        if isinstance(pi, str) and pi.startswith("pi_"):
            pio = stripe.PaymentIntent.retrieve(pi)
            pc = getattr(pio, "customer", None)
            if pc and str(pc).startswith("cus_"):
                return str(pc)
    except Exception:
        pass

    details = obj.get("customer_details")
    email = ""
    if isinstance(details, dict):
        email = (details.get("email") or "").strip()
    if not email:
        email = (obj.get("customer_email") or "").strip()
    if email:
        try:
            lst = stripe.Customer.list(email=email, limit=5)
            for customer in lst.data:
                cu = getattr(customer, "id", "")
                if isinstance(cu, str) and cu.startswith("cus_"):
                    return cu
            # Guest checkout: no Stripe Customer yet — create cus_ for DB entitlements (SQLite key).
            created = stripe.Customer.create(
                email=email,
                metadata={"glb_provisioned": "guest_checkout_email"},
            )
            cnew = getattr(created, "id", None)
            if isinstance(cnew, str) and cnew.startswith("cus_"):
                return cnew
        except Exception:
            pass
    return None


def _checkout_line_items_include_travel_price(session_id: str) -> bool:
    if not STRIPE_TRAVEL_PRICE_IDS or not session_id.startswith("cs_"):
        return False
    try:
        lines = stripe.checkout.Session.list_line_items(session_id, limit=100)
        for li in lines.auto_paging_iter():
            price = getattr(li, "price", None)
            if price is None:
                continue
            pid = getattr(price, "id", None)
            if pid and str(pid) in STRIPE_TRAVEL_PRICE_IDS:
                return True
    except Exception:
        pass
    return False


def _stripe_checkout_session_payment_hold(session_id: str) -> Optional[str]:
    """Return hold reason while Checkout Session is not settled (open / unpaid)."""
    if not session_id.startswith("cs_") or not STRIPE_SECRET_KEY:
        return None
    try:
        sess = stripe.checkout.Session.retrieve(session_id)
        st = getattr(sess, "status", None)
        ps = getattr(sess, "payment_status", None)
        if st == "open":
            return "payment_processing"
        if st == "complete" and ps == "unpaid":
            return "payment_processing"
    except Exception:
        pass
    return None


def apply_checkout_session_completed(obj: dict[str, Any]) -> None:
    """payment-mode Payment Link: customer may be null in webhook; travel is not on subscriptions."""
    ps = (obj.get("payment_status") or "").strip()
    if ps not in ("paid", "complete", "no_payment_required"):
        return
    sid = obj.get("id")
    if not isinstance(sid, str) or not sid.startswith("cs_"):
        return
    cid = _resolve_customer_id_from_checkout(obj)
    if not cid:
        return
    recompute_customer(cid)
    if obj.get("mode") != "payment":
        return
    if not _checkout_line_items_include_travel_price(sid):
        return
    r = _row(cid)
    core = int(r["core_subscribed"]) if r else 0
    travel = max(int(r["travel_active"]) if r else 0, 1)
    st = (r["subscription_status"] or "") if r else ""
    pf = int(r["payment_failed"]) if r else 0
    fa = float(r["payment_failed_at"]) if r and r["payment_failed_at"] is not None else None
    gu = float(r["grace_until"]) if r and r["grace_until"] is not None else None
    _upsert_row(cid, core, travel, st, pf, fa, gu)


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


class OpsActionBody(BaseModel):
    target: Optional[str] = None


@app.post("/billing/portal")
async def billing_portal(request: Request, body: PortalBody):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "STRIPE_SECRET_KEY not configured")
    cid = (body.customer_id or "").strip()
    if not cid.startswith("cus_"):
        raise HTTPException(400, "invalid customer_id")
    preflight_body = json.dumps(
        {"action": "payment_action", "route": "/billing/portal", "customer_id": cid}
    ).encode("utf-8")
    try:
        _, payment_audit = preflight_reinject_loop(
            preflight_body,
            route="/billing/portal",
            upstream_target="stripe.billing_portal.Session.create",
        )
        lock_cfg = load_external_lock()
        if payment_action_requires_ore_approval(lock_cfg) and not ore_approval_present(request):
            hold_meta = dict(payment_audit)
            hold_meta["result"] = "HOLD"
            hold_meta["reason"] = "ORE_APPROVAL_REQUIRED_FOR_PAYMENT_ACTION"
            append_audit_log(hold_meta)
            emit_bee_fix_for_hold(hold_meta)
            return JSONResponse(
                status_code=403,
                content={
                    "STATE": "HOLD",
                    "REASON": "ORE_APPROVAL_REQUIRED_FOR_PAYMENT_ACTION",
                    "NEXT_ACTION": "SELF_FIX_NOW",
                },
            )
        append_audit_log(payment_audit)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "STATE": "HOLD",
                "REASON": str(e),
                "NEXT_ACTION": "SELF_FIX_NOW",
            },
        )
    try:
        sess = stripe.billing_portal.Session.create(
            customer=cid,
            return_url=PORTAL_RETURN_URL,
        )
        return {"url": sess.url}
    except Exception as e:
        raise HTTPException(502, str(e)) from e


@app.post("/create-portal-session")
async def create_portal_session_alias(request: Request, body: PortalBody):
    return await billing_portal(request, body)


def action_requires_ore_approval(lock_cfg: dict[str, Any], action_name: str) -> bool:
    boundary = lock_cfg.get("approval_boundary", {})
    required = boundary.get("ore_approval_required_for", [])
    return action_name in required


async def guarded_ops_action(
    request: Request,
    action_name: str,
    route: str,
    target: str,
) -> JSONResponse:
    preflight_body = json.dumps(
        {"action": action_name, "route": route, "target": target}
    ).encode("utf-8")
    try:
        _, ops_audit = preflight_reinject_loop(
            preflight_body,
            route=route,
            upstream_target=f"ops.{action_name}",
        )
        lock_cfg = load_external_lock()
        if action_requires_ore_approval(lock_cfg, action_name) and not ore_approval_present(request):
            hold_meta = dict(ops_audit)
            hold_meta["result"] = "HOLD"
            hold_meta["reason"] = f"ORE_APPROVAL_REQUIRED_FOR_{action_name.upper()}"
            append_audit_log(hold_meta)
            emit_bee_fix_for_hold(hold_meta)
            return JSONResponse(
                status_code=403,
                content={
                    "STATE": "HOLD",
                    "REASON": f"ORE_APPROVAL_REQUIRED_FOR_{action_name.upper()}",
                    "NEXT_ACTION": "SELF_FIX_NOW",
                },
            )
        append_audit_log(ops_audit)
        # Hard lock: never execute real deploy/release commands in this service.
        return JSONResponse(
            status_code=200,
            content={
                "STATE": "PASS",
                "ACTION": action_name,
                "EXECUTED": False,
                "REASON": "GATE_PASSED_COMMAND_EXECUTION_DISABLED",
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "STATE": "HOLD",
                "REASON": str(e),
                "NEXT_ACTION": "SELF_FIX_NOW",
            },
        )


@app.post("/ops/deploy")
async def ops_deploy(request: Request, body: OpsActionBody):
    target = (body.target or "production").strip() or "production"
    return await guarded_ops_action(request, "production_deploy", "/ops/deploy", target)


@app.post("/ops/release")
async def ops_release(request: Request, body: OpsActionBody):
    target = (body.target or "release").strip() or "release"
    return await guarded_ops_action(request, "release_action", "/ops/release", target)


async def get_entitlements(
    customer_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict[str, Any]:
    """Resolve Stripe entitlements and a gate ``status``: PASS | HOLD | INVALID."""
    if not STRIPE_SECRET_KEY:
        return {
            "status": "INVALID",
            "reason": "stripe_not_configured",
            "ok": False,
            "core_subscribed": False,
            "travel_active": False,
        }

    cid = (customer_id or "").strip()
    sid = (session_id or "").strip()

    ph = _stripe_checkout_session_payment_hold(sid) if sid.startswith("cs_") else None
    if ph:
        return {
            "status": "HOLD",
            "reason": ph,
            "ok": False,
            "core_subscribed": False,
            "travel_active": False,
        }

    if sid.startswith("cs_"):
        try:
            checkout = stripe.checkout.Session.retrieve(
                sid, expand=["customer", "payment_intent", "subscription"]
            )
            session_obj = _session_as_dict(checkout)
            if session_obj.get("id"):
                apply_checkout_session_completed(session_obj)
                rcid = _resolve_customer_id_from_checkout(session_obj)
                if rcid:
                    cid = rcid
        except Exception:
            pass

    if not cid or not cid.startswith("cus_"):
        return {
            "status": "HOLD",
            "reason": "missing_customer",
            "ok": False,
            "core_subscribed": False,
            "travel_active": False,
        }

    try:
        sync_from_stripe_customer(cid)
    except Exception:
        pass

    data = compute_entitlement_response(cid)
    allowed = bool(
        data.get("ok")
        and (data.get("core_subscribed") or data.get("travel_active"))
    )
    if allowed:
        return {**data, "status": "PASS"}
    return {
        **data,
        "status": "HOLD",
        "reason": "insufficient_entitlement",
    }


@app.get("/entitlements")
async def entitlements(customer_id: Optional[str] = None, session_id: Optional[str] = None):
    return await get_entitlements(customer_id=customer_id, session_id=session_id)


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature") or ""

    try:
        event = _event_payload(payload, sig)
    except ValueError as e:
        raise HTTPException(400, f"invalid payload: {e}") from e
    except json.JSONDecodeError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(400, f"invalid signature: {e}") from e

    et = str(event.get("type") or "")
    data = event.get("data")
    if not isinstance(data, dict):
        data = {}
    obj = data.get("object")
    if not isinstance(obj, dict):
        obj = {}

    handler_err: str | None = None
    try:
        if et == "customer.subscription.updated":
            cid = obj.get("customer")
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
            apply_checkout_session_completed(obj)
    except Exception as e:
        handler_err = f"{type(e).__name__}: {e}"

    out: dict[str, Any] = {"received": True, "type": et}
    if handler_err:
        out["handler_error"] = handler_err[:800]
    return out


async def mandatory_translate_gateway(
    prompt: str,
    session_id: Optional[str],
    forward_fields: dict[str, Any],
) -> Response:
    """Upstream translate with context-aware prompt (billing-side gateway)."""
    if not TRANSLATE_PROXY_URL:
        raise HTTPException(
            501,
            "TRANSLATE_PROXY_URL not set; configure upstream or deploy merged translate",
        )
    payload = dict(forward_fields)
    payload["text"] = prompt
    if session_id:
        payload["session_id"] = session_id
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    body, audit_meta = preflight_reinject_loop(
        body,
        route="/translate",
        upstream_target=f"{TRANSLATE_PROXY_URL}/translate",
    )
    append_audit_log(audit_meta)
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{TRANSLATE_PROXY_URL}/translate",
            content=body,
            headers={"Content-Type": "application/json"},
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json"),
    )


@app.post("/translate")
async def translate_proxy(request: Request):
    if not TRANSLATE_PROXY_URL:
        raise HTTPException(
            501,
            "TRANSLATE_PROXY_URL not set; configure upstream or deploy merged translate",
        )

    raw = await request.body()
    body_json: dict[str, Any] = {}
    try:
        ct = (request.headers.get("content-type") or "").lower()
        if raw and ("json" in ct or raw[:1] in (b"{", b"[")):
            body_json = json.loads(raw.decode("utf-8"))
    except Exception:
        body_json = {}

    cid_in = (
        body_json.get("customer_id")
        or body_json.get("client_id")
        or body_json.get("stripe_customer_id")
    )
    sid_in = body_json.get("session_id")
    entitlement = await get_entitlements(customer_id=cid_in, session_id=sid_in)
    if entitlement.get("status") != "PASS":
        return JSONResponse(status_code=200, content=entitlement)

    lang = body_json.get("lang") or "日本語"
    text = body_json.get("text") or ""
    prompt = (
        "### 空気読みロジック(Context-Aware) ###\n"
        f"以下のテキストを{lang}に翻訳せよ。\n"
        f"テキスト: {text}"
    )
    try:
        return await mandatory_translate_gateway(
            prompt=prompt,
            session_id=sid_in if isinstance(sid_in, str) else None,
            forward_fields=body_json,
        )
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "STATE": "HOLD",
                "REASON": str(e),
                "NEXT_ACTION": "SELF_FIX_NOW",
            },
        )


@app.get("/health")
async def health():
    return {"ok": True, "billing_db": DB_PATH}

