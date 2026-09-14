import json
from pathlib import Path
import unittest

class ExecutiveGeometryTest(unittest.TestCase):
    def test_chart_headlines_do_not_overlap_each_other_or_summary(self):
        root = Path(__file__).resolve().parents[3]
        template = json.loads((root / "templates/executive/template.json").read_text())
        layout = next(x for x in template["layouts"] if x["id"] == "title_chart_metrics_cards_8029")
        headings = [c for c in layout["components"] if c["id"].startswith("title_and_summary_part_") and not c["id"].endswith("_5")]
        boxes = [(c["position"]["x"], c["position"]["y"], c["elements"][0]["size"]["width"], c["elements"][0]["size"]["height"]) for c in headings]
        for i, (x, y, w, h) in enumerate(boxes):
            self.assertLessEqual(y + h, 179)
            for xx, yy, ww, hh in boxes[i + 1:]:
                self.assertTrue(x + w <= xx or xx + ww <= x or y + h <= yy or yy + hh <= y)
        variants = {v["id"]: v for c in template["merged_components"] for v in c["variants"]}
        for c in headings:
            self.assertEqual(c, variants[c["id"]])

if __name__ == "__main__": unittest.main()
