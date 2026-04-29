import importlib
import json
import os
import tempfile
import uuid
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from starlette.responses import Response

from smile_friend_engine.quota_sqlite import SqliteDailyQuota


def _reload_main(env: dict[str, str]):
    for k, v in env.items():
        os.environ[k] = v
    # Ensure stale env from other tests does not select wrong translate path
    if "GLB_TRANSLATE_CALLABLE" not in env:
        os.environ.pop("GLB_TRANSLATE_CALLABLE", None)
    if "GLB_QUOTA_BACKEND" not in env:
        os.environ["GLB_QUOTA_BACKEND"] = "sqlite"
    import smile_friend_engine.main as m

    importlib.reload(m)
    return m


class SqliteQuotaStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.tmp.close()
        self.path = self.tmp.name
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))
        self.store = SqliteDailyQuota(self.path)

    def test_sixth_request_blocked_after_five(self) -> None:
        day = "2026-04-29"
        cid = str(uuid.uuid4())
        for i in range(5):
            ok, n = self.store.try_consume_one(cid, day, 5)
            self.assertTrue(ok, f"iteration {i}")
            self.assertEqual(n, i + 1)
        ok6, n6 = self.store.try_consume_one(cid, day, 5)
        self.assertFalse(ok6)
        self.assertEqual(n6, 5)

    def test_persist_across_reopen_same_file(self) -> None:
        day = "2026-04-30"
        cid = str(uuid.uuid4())
        for _ in range(3):
            self.store.try_consume_one(cid, day, 5)
        s2 = SqliteDailyQuota(self.path)
        ok, n = s2.try_consume_one(cid, day, 5)
        self.assertTrue(ok)
        self.assertEqual(n, 4)


class TranslateEndpointTests(unittest.TestCase):
    def test_sixth_translate_returns_429(self) -> None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        tmp.close()
        self.addCleanup(lambda: os.path.exists(tmp.name) and os.remove(tmp.name))

        async def fake_dispatch(raw: bytes, ct: str, body_json: dict) -> Response:
            return Response(
                content=json.dumps({"translatedText": "ok", "ok": True}).encode("utf-8"),
                status_code=200,
                media_type="application/json",
            )

        m = _reload_main(
            {
                "GLB_FREE_QUOTA_DB_PATH": tmp.name,
                "GLB_FREE_DAILY": "5",
                "TRANSLATE_UPSTREAM_URL": "https://example.invalid",
                "BILLING_ENTITLEMENTS_BASE": "",
            }
        )
        c = str(uuid.uuid4())
        with patch.object(m, "dispatch_translate", side_effect=fake_dispatch):
            with patch.object(m, "customer_is_unlimited", new=AsyncMock(return_value=False)):
                client = TestClient(m.app)
                with patch.object(m, "utc_day_iso", return_value="2026-06-01"):
                    for i in range(5):
                        r = client.post(
                            "/translate",
                            json={
                                "client_id": c,
                                "text": "h",
                                "source": "en",
                                "target": "de",
                            },
                        )
                        self.assertEqual(r.status_code, 200, f"call {i}")
                    r6 = client.post(
                        "/translate",
                        json={
                            "client_id": c,
                            "text": "h",
                            "source": "en",
                            "target": "de",
                        },
                    )
                    self.assertEqual(r6.status_code, 429)
                    self.assertEqual(r6.json().get("error"), "FREE_LIMIT_REACHED")

    def test_paid_customer_no_429_many_calls(self) -> None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        tmp.close()
        self.addCleanup(lambda: os.path.exists(tmp.name) and os.remove(tmp.name))

        async def fake_dispatch(raw: bytes, ct: str, body_json: dict) -> Response:
            return Response(
                content=json.dumps({"translatedText": "ok"}).encode("utf-8"),
                status_code=200,
                media_type="application/json",
            )

        m = _reload_main(
            {
                "GLB_FREE_QUOTA_DB_PATH": tmp.name,
                "GLB_FREE_DAILY": "5",
                "TRANSLATE_UPSTREAM_URL": "https://example.invalid",
                "BILLING_ENTITLEMENTS_BASE": "",
            }
        )
        c = str(uuid.uuid4())
        with patch.object(m, "dispatch_translate", side_effect=fake_dispatch):
            with patch.object(m, "customer_is_unlimited", new=AsyncMock(return_value=True)):
                client = TestClient(m.app)
                for i in range(12):
                    r = client.post(
                        "/translate",
                        json={
                            "client_id": c,
                            "customer_id": "cus_test_unlimited",
                            "text": "h",
                            "source": "en",
                            "target": "de",
                        },
                    )
                    self.assertEqual(r.status_code, 200, f"iter {i}")


if __name__ == "__main__":
    unittest.main()
