from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from training.css.encoding import Schema, encode, windows, padded_window, IGNORE
from training.css.prepare import assign_groups, prepare, file_hash


ROOT = Path(__file__).resolve().parents[3]


class EncodingTests(unittest.TestCase):
    def setUp(self):
        self.schema = Schema.load(ROOT / "packs/css/schema.json")

    def record(self):
        source = '/* 🌌 */\r\n.a { content: "星"; }\r\n'
        pieces = [("/* 🌌 */", "comment"), (".a", "class"), ("{", "punctuation"),
                  ("content", "property"), (":", "punctuation"), ('"星"', "string"),
                  (";", "punctuation"), ("}", "punctuation")]
        spans, cursor = [], 0
        for text, role in pieces:
            start = source.index(text, cursor)
            cursor = start + len(text)
            unit = lambda index: len(source[:index].encode("utf-16-le")) // 2
            span = {"start": unit(start), "end": unit(cursor), "tokenType": role}
            if role == "property":
                span["modifiers"] = ["declaration"]
            spans.append(span)
        return {"documentKind": "css", "source": source,
                "contentHash": hashlib.sha256(source.encode()).hexdigest(),
                "result": {"offsetEncoding": "utf-16", "spans": spans}}

    def test_utf16_utf8_crlf_and_modifier_masks(self):
        doc = self.record()
        encoded = encode(doc, self.schema)
        self.assertEqual(bytes(list(encoded.columns["input_ids"])).decode("utf-8"), doc["source"])
        begin = doc["source"].encode().index(b"content")
        self.assertEqual(encoded.columns["modifier_bits"][begin], 1)
        self.assertTrue(all(value == 0 for value in encoded.columns["modifier_bits"][begin + 1:begin + 7]))
        byte = 0
        for char in doc["source"]:
            for continuation in range(1, len(char.encode())):
                self.assertEqual(encoded.columns["boundary_labels"][byte + continuation], IGNORE)
            byte += len(char.encode())
        lo, hi = windows(encoded, 512, True)[0][0]
        self.assertEqual(len(padded_window(encoded, lo, hi, 512)["input_ids"]), 512)

    def test_rejects_split_surrogates_gaps_and_changed_sources(self):
        doc = self.record()
        broken = copy.deepcopy(doc)
        broken["result"]["spans"][0]["end"] = 4
        with self.assertRaises(ValueError):
            encode(broken, self.schema)
        broken = copy.deepcopy(doc)
        broken["result"]["spans"].pop()
        with self.assertRaises(ValueError):
            encode(broken, self.schema)
        broken = copy.deepcopy(doc)
        broken["source"] += "x"
        with self.assertRaises(ValueError):
            encode(broken, self.schema)

    def test_evaluation_windows_never_use_gold_boundaries(self):
        source = "a" * 480 + "星" * 30 + "b" * 50
        doc = {"documentKind": "scss", "source": source,
               "contentHash": hashlib.sha256(source.encode()).hexdigest(),
               "result": {"offsetEncoding": "utf-16", "spans": [
                   {"start": 0, "end": 480, "tokenType": "comment"},
                   {"start": 480, "end": len(source), "tokenType": "string"}]}}
        encoded = encode(doc, self.schema)
        fixed, _ = windows(encoded, 512, False)
        adaptive, _ = windows(encoded, 512, True)
        self.assertNotEqual(fixed, adaptive)
        self.assertEqual(adaptive[0][1], 480)
        for lo, hi in fixed:
            source.encode()[lo:hi].decode("utf-8")
        shifted = copy.deepcopy(doc)
        shifted["result"]["spans"] = [{"start": 0, "end": len(source), "tokenType": "string"}]
        self.assertEqual(windows(encode(shifted, self.schema), 512, False)[0], fixed)

    def test_grouped_allocation_is_deterministic_and_covers_each_kind(self):
        weights = {f"source:{index}": Counter(css=10 + index, scss=4 + index, less=3 + index)
                   for index in range(20)}
        first = assign_groups(weights, 42)
        self.assertEqual(first, assign_groups(dict(reversed(list(weights.items()))), 42))
        self.assertEqual(set(first), set(weights))
        self.assertEqual(set(first.values()), {"train", "validation", "test"})
        with self.assertRaises(ValueError):
            assign_groups({"one": Counter(css=3, scss=3, less=3)}, 42)


class SnapshotTests(unittest.TestCase):
    def test_copy_exclusion_replay_and_corruption_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "css"
            folder = root / "gold/input"
            folder.mkdir(parents=True)
            records = []
            for kind in ("css", "scss", "less"):
                for index in range(12):
                    value = f"token{kind}{index}"
                    source = f".node {{ value: {value}; }}"
                    pieces = [(".node", "class"), ("{", "punctuation"), ("value", "property"),
                              (":", "punctuation"), (value, "keyword"), (";", "punctuation"), ("}", "punctuation")]
                    spans, cursor = [], 0
                    for text, role in pieces:
                        at = source.index(text, cursor)
                        cursor = at + len(text)
                        spans.append({"start": at, "end": cursor, "tokenType": role})
                    records.append({"documentKind": kind, "source": source,
                        "contentHash": hashlib.sha256(source.encode()).hexdigest(),
                        "sourceGroup": f"project:{kind}{index}", "repository": "project", "path": f"{kind}{index}.{kind}",
                        "result": {"offsetEncoding": "utf-16", "spans": spans}})
            duplicate = copy.deepcopy(records[0])
            duplicate["source"] = duplicate["source"].replace(".node", ".copy")
            duplicate["contentHash"] = hashlib.sha256(duplicate["source"].encode()).hexdigest()
            duplicate["sourceGroup"] = "another:group"
            duplicate["path"] = "copy.css"
            records.append(duplicate)
            gold = folder / "labeled-sample.jsonl"
            gold.write_text("".join(json.dumps(record) + "\n" for record in records))
            manifest = {"files": len(records), "checksums": {"labeled-sample.jsonl": file_hash(gold)},
                        "provenance": {"schemaHash": file_hash(ROOT / "packs/css/schema.json"),
                            "semanticContractHash": file_hash(ROOT / "packs/css/SEMANTICS.md")}}
            (folder / "sample.json").write_text(json.dumps(manifest))
            (root / "current-gold.json").write_text(json.dumps({"directory": "gold/input",
                "manifestHash": file_hash(folder / "sample.json")}))
            first = prepare(root)
            self.assertEqual(first["excludedCopyDocuments"], 2)
            self.assertEqual(first["retainedDocuments"], 35)
            for split in ("train", "validation", "test"):
                for kind in ("css", "scss", "less"):
                    self.assertGreater(first["splits"][split]["documentKinds"][kind]["documents"], 0)
            self.assertEqual(prepare(root), first)
            path = root / "prepared" / first["snapshot"] / "train/input_ids.bin"
            path.write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "corrupt"):
                prepare(root)


if __name__ == "__main__":
    unittest.main()
