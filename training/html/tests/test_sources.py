import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from packs.html.dataset import fetch_sources


class SourceTests(unittest.TestCase):
    def fixture(self, folder: Path):
        config = folder / "config.json"
        config.write_text(json.dumps({"sources": [{"id": "mdn-test", "repository": "mdn/test", "commit": "f"*40, "prefixes": ["modern/"]}]}))
        content = b'<dialog open>Ready</dialog>'
        sha = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content, usedforsecurity=False).hexdigest()
        tree = {"sha": "a"*40, "truncated": False, "tree": [
            {"path": "modern/index.html", "type": "blob", "mode": "100644", "size": len(content), "sha": sha},
            {"path": "images/image.jpg", "type": "blob", "mode": "100644", "sha": "not-fetched"}]}
        def download(url, _limit):
            return json.dumps(tree).encode() if "api.github.com" in url else content
        return config, content, tree, download

    def test_pinned_blob_identity_reuse_and_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config, content, _, download = self.fixture(base)
            root = base / "sources"
            with patch.object(fetch_sources, "download", side_effect=download): fetch_sources.fetch(root, config)
            source = root / ("mdn-test-" + "f"*12) / "modern/index.html"
            self.assertEqual(source.read_bytes(), content)
            with patch.object(fetch_sources, "download", side_effect=AssertionError("must reuse")): fetch_sources.fetch(root, config)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "modified"): fetch_sources.fetch(root, config)

    def test_bad_git_blob_or_unsafe_path_never_publishes(self):
        for kind in ("blob", "path"):
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                config, _, tree, download = self.fixture(base)
                if kind == "blob": tree["tree"][0]["sha"] = "wrong"
                else: tree["tree"][0]["path"] = "../../escape.html"
                root = base / "sources"
                with patch.object(fetch_sources, "download", side_effect=download), self.assertRaises(ValueError): fetch_sources.fetch(root, config)
                self.assertFalse((root / ("mdn-test-" + "f"*12)).exists())
                self.assertFalse((root / ".fetch.lock").exists())


if __name__ == "__main__": unittest.main()
