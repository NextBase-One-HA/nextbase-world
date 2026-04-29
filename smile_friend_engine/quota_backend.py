"""Select Firestore vs SQLite quota backend."""

from __future__ import annotations

import os


def quota_backend_name() -> str:
    explicit = (os.getenv("GLB_QUOTA_BACKEND") or "").strip().lower()
    if explicit in ("firestore", "sqlite"):
        return explicit
    if _project_available():
        return "firestore"
    return "sqlite"


def _project_available() -> bool:
    return bool(
        (os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
        or (os.getenv("GCLOUD_PROJECT") or "").strip()
    )
