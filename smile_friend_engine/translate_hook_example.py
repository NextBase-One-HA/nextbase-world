"""
Example hook for GLB_TRANSLATE_CALLABLE (copy/rename; wire your real translate here).

  export GLB_TRANSLATE_CALLABLE=smile_friend_engine.translate_hook_example:run_translate

Replace the body of run_translate with your existing smile-friend-engine translate implementation
(Gemini, Vertex, etc.) — return a JSON Response with the same shape your clients expect.
"""

from __future__ import annotations

from typing import Any

from starlette.responses import JSONResponse, Response


async def run_translate(raw: bytes, content_type: str, body_json: dict[str, Any]) -> Response:
    # Placeholder: replace with your in-service translate call.
    _ = (raw, content_type)
    return JSONResponse(
        {
            "ok": True,
            "translatedText": f"[example] {body_json.get('text', '')}",
            "routeType": "example",
        }
    )
