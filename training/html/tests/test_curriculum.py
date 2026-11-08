import json
from pathlib import Path
import tempfile
import unittest

from packs.html.dataset.generate_curriculum import examples, generate
from training.html.prepare import assign_groups
from collections import Counter


class CurriculumTests(unittest.TestCase):
    def test_immutable_generation_replay_and_original_source_forms(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "curriculum"
            generate(root, 4)
            saved = (root / "source.lock.json").read_bytes()
            generate(root, 4)
            self.assertEqual((root / "source.lock.json").read_bytes(), saved)
            lock = json.loads(saved)
            self.assertEqual(len(lock["files"]), 56)
            self.assertIn(b"\r\n", (root / "attribute-forms/example-000.html").read_bytes())
            self.assertIn("<strong", examples(1)["javascript-strings"])
            (root / "attribute-forms/example-000.html").write_text("changed")
            with self.assertRaisesRegex(ValueError, "modified"): generate(root, 4)

    def test_stream_balancing_keeps_natural_and_focus_in_each_holdout(self):
        weights = {f"natural:{i}": Counter({"html:natural": i+5}) for i in range(8)}
        weights.update({f"focus:{i}": Counter({"html:focus": i+5}) for i in range(8)})
        assignments = assign_groups(weights, 1729)
        for split in ("train", "validation", "test"):
            self.assertTrue(any(g.startswith("natural:") and fold == split for g, fold in assignments.items()))
            self.assertTrue(any(g.startswith("focus:") and fold == split for g, fold in assignments.items()))


if __name__ == "__main__": unittest.main()
