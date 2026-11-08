import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from packs.css.dataset import fetch_sources


class SourceTests(unittest.TestCase):
    def fixture(self, base: Path, member: str = "package/scss/theme.scss", bad_integrity=False):
        spec = {"name": "example", "version": "1.2.3", "directory": "example-1.2.3",
                "prefix": "scss/", "suffix": ".scss"}
        config = base / "packages.json"
        config.write_text(json.dumps({"packages": [spec]}))
        content = b"$gap: 4px; .card { gap: $gap; }\n"
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            item = tarfile.TarInfo(member)
            item.size = len(content)
            archive.addfile(item, io.BytesIO(content))
        raw = buffer.getvalue()
        integrity = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode()
        metadata = {"name": "example", "version": "1.2.3", "license": "MIT",
                    "dist": {"tarball": "https://registry.npmjs.org/example/-/example-1.2.3.tgz",
                             "integrity": "sha512-bad" if bad_integrity else integrity}}
        return config, content, [json.dumps(metadata).encode(), raw]

    def test_verified_source_replay_and_modified_source_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config, content, responses = self.fixture(base)
            root = base / "sources"
            with patch.object(fetch_sources, "download", side_effect=responses):
                fetch_sources.fetch(root, config)
            source = root / "example-1.2.3/scss/theme.scss"
            self.assertEqual(source.read_bytes(), content)
            with patch.object(fetch_sources, "download", side_effect=AssertionError("must reuse locked source")):
                fetch_sources.fetch(root, config)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "modified"):
                fetch_sources.fetch(root, config)
            self.assertFalse((root / ".fetch.lock").exists())

    def test_rejects_bad_integrity_without_publishing(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config, _, responses = self.fixture(base, bad_integrity=True)
            root = base / "sources"
            with patch.object(fetch_sources, "download", side_effect=responses):
                with self.assertRaisesRegex(ValueError, "integrity"):
                    fetch_sources.fetch(root, config)
            self.assertFalse((root / "example-1.2.3").exists())
            self.assertFalse((root / ".fetch.lock").exists())

    def test_rejects_archive_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config, _, responses = self.fixture(base, member="package/../../escape.scss")
            root = base / "sources"
            with patch.object(fetch_sources, "download", side_effect=responses):
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    fetch_sources.fetch(root, config)
            self.assertFalse((base / "escape.scss").exists())
            self.assertFalse((root / "example-1.2.3").exists())


if __name__ == "__main__":
    unittest.main()
