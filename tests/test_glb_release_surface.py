import unittest
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


class ReleaseSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index_next = (ROOT / "index.next.html").read_text(encoding="utf-8")
        self.index_free = (ROOT / "index.html").read_text(encoding="utf-8")
        self.travel_data = json.loads((ROOT / "canonical" / "travel_mode_minimal.json").read_text(encoding="utf-8"))

    def test_has_required_cta_and_events(self) -> None:
        required = [
            "Start GLB 2.99",
            "payment_cta_click",
            "purchase_success",
            "user_drop_point",
            "translation_success",
            "translation_failure",
            "api_failure",
        ]
        for token in required:
            self.assertIn(token, self.index_next)

    def test_travel_mode_flag_and_categories(self) -> None:
        self.assertIn("NEXTBASE_TRAVEL_MODE_FULL", self.index_next)
        self.assertIn("canonical/travel_mode_minimal.json", self.index_next)
        self.assertIn("travel_mode_entry", self.index_next)
        self.assertIn("travel_phrase_used", self.index_next)

    def test_core_flow_route_order_is_kept(self) -> None:
        start = self.index_next.find("var cached = readTxCache(text, source, target);")
        self.assertNotEqual(start, -1, "missing cached route section")
        flow = self.index_next[start:]
        points = [
            "var cached = readTxCache(text, source, target);",
            "var localOut = tryLocalRoute(text, source, target);",
            "if (!canGlbTranslate())",
            "if (!pivot) {",
            "fetchTranslate(text, source, target)",
            "fetchTranslate(text, source, 'en')",
        ]
        indices = []
        for point in points:
            idx = flow.find(point)
            self.assertNotEqual(idx, -1, f"missing flow point: {point}")
            indices.append(idx)
        self.assertEqual(indices, sorted(indices))

    def test_free_page_routes_to_core_for_payment(self) -> None:
        self.assertTrue(
            "index.2.99.html#glb-core-subscribe-block" in self.index_free
            or "index.next.html#glb-core-subscribe-block" in self.index_free
        )
        self.assertTrue(
            "Start GLB 2.99" in self.index_free or "Start Core" in self.index_free,
            "index.html should surface a Core checkout CTA (legacy or LP copy)",
        )

    def test_travel_data_schema_and_actions(self) -> None:
        categories = self.travel_data.get("categories", [])
        self.assertEqual(len(categories), 12)
        required_item_keys = {
            "intent_id",
            "user_intent_ja",
            "japanese_phrase",
            "translated_phrase",
            "show_to_staff_text",
            "voice_output_text",
            "safe_polite_phrase",
            "emergency_short_phrase",
            "next_actions",
        }
        banned = ["[cite_start]", "[cite:"]
        for cat in categories:
            self.assertIn("icon", cat)
            self.assertIn("priority", cat)
            self.assertTrue(isinstance(cat.get("items"), list) and len(cat["items"]) > 0)
            item = cat["items"][0]
            self.assertTrue(required_item_keys.issubset(set(item.keys())))
            self.assertLessEqual(len(item.get("next_actions", [])), 3)
            payload = json.dumps(item, ensure_ascii=False)
            for token in banned:
                self.assertNotIn(token, payload)
        emergency = next(x for x in categories if x["category"] == "Emergency")["items"][0]
        trouble = next(x for x in categories if x["category"] == "Trouble")["items"][0]
        self.assertIn("住所やホテル名を見せる", emergency["next_actions"])
        self.assertIn("大使館情報を確認する", trouble["next_actions"])


if __name__ == "__main__":
    unittest.main()
