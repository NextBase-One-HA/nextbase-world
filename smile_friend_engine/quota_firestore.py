"""
Firestore free-tier quota: collection ``quotas``, document id = ``client_id``.

Fields:
  - count (int)
  - lastResetDate (YYYY-MM-DD in UTC)

Logic (transactional):
  1. Read doc
  2. If ``lastResetDate`` != today → treat count as 0 for limit check, then write today
  3. If count >= limit → return False (caller returns 429)
  4. Else increment count and set lastResetDate to today → return True
"""

from __future__ import annotations

import os
from typing import Optional

from google.cloud import firestore


def _collection_name() -> str:
    return (os.getenv("GLB_FIRESTORE_QUOTA_COLLECTION") or "quotas").strip() or "quotas"


def _project_id() -> Optional[str]:
    return (os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT") or "").strip() or None


_client: Optional[firestore.Client] = None


def _get_client() -> firestore.Client:
    global _client
    if _client is None:
        pid = _project_id()
        _client = firestore.Client(project=pid) if pid else firestore.Client()
    return _client


def try_increment_free_quota(client_id: str, today: str, limit: int) -> bool:
    """
    Returns True if the translate request is allowed (count incremented).
    Returns False if already at limit (6th free request when limit=5).
    """
    db = _get_client()
    ref = db.collection(_collection_name()).document(client_id)
    transaction = db.transaction()

    @firestore.transactional
    def _apply(transaction, doc_ref, day: str, lim: int) -> bool:
        snap = doc_ref.get(transaction=transaction)
        if snap.exists:
            data = snap.to_dict() or {}
            count = int(data.get("count") or 0)
            last_reset = str(data.get("lastResetDate") or "")
        else:
            count = 0
            last_reset = ""

        if last_reset != day:
            count = 0

        if count >= lim:
            return False

        transaction.set(
            doc_ref,
            {"count": count + 1, "lastResetDate": day},
            merge=True,
        )
        return True

    return _apply(transaction, ref, today, limit)
