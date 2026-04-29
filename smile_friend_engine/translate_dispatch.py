"""
Resolve how /translate runs **after** quota — without forcing a second HTTP service.

Resolution order:
1. ``GLB_TRANSLATE_CALLABLE`` — ``package.module:function_name`` pointing to an async
   ``(raw_bytes, content_type, body_json) -> starlette.responses.Response``.
   Use this for inline translate logic already inside smile-friend-engine (no extra hop).
2. Else ``TRANSLATE_UPSTREAM_URL`` — optional legacy proxy to ``{base}/translate``.
3. Else HTTP 501 with configuration hint.
"""

from __future__ import annotations

import importlib
import os
from typing import Any

import httpx
from fastapi import HTTPException
from starlette.responses import Response


async def dispatch_translate(raw: bytes, content_type: str, body_json: dict[str, Any]) -> Response:
    spec = (os.getenv("GLB_TRANSLATE_CALLABLE") or "").strip()
    if spec:
        if ":" not in spec:
            raise HTTPException(
                501,
                "GLB_TRANSLATE_CALLABLE must look like mypackage.translate:handle_translate",
            )
        mod_name, _, attr = spec.partition(":")
        try:
            module = importlib.import_module(mod_name.strip())
            fn = getattr(module, attr.strip())
        except Exception as e:
            raise HTTPException(501, f"GLB_TRANSLATE_CALLABLE import failed: {e}") from e
        return await fn(raw, content_type, body_json)

    upstream = (os.getenv("TRANSLATE_UPSTREAM_URL") or "").rstrip("/")
    if upstream:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{upstream}/translate",
                content=raw,
                headers={"Content-Type": content_type or "application/json"},
            )
        return Response(
            content=r.content,
            status_code=r.status_code,
            media_type=r.headers.get("content-type", "application/json"),
        )

    raise HTTPException(
        501,
        "Configure GLB_TRANSLATE_CALLABLE (in-process translate) or TRANSLATE_UPSTREAM_URL (proxy).",
    )
