from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from training.html.encoding import Schema, encode, windows, IGNORE
from training.html.prepare import REPOSITORY, assign_groups, file_hash, prepare


def record(index=1):
    parts = [("<", "punctuation", []), ("p", "tag", []), (">", "punctuation", [])] * index
    parts += [("🌌 " + str(index), "text", [])]
    parts += [("</", "punctuation", []), ("p", "tag", ["closing"]), (">", "punctuation", [])] * index
    source, spans, unit = "", [], 0
    for text, role, modifiers in parts:
        start = unit
        source += text
        unit += len(text.encode("utf-16-le")) // 2
        spans.append({"start": start, "end": unit, "tokenType": role, **({"modifiers": modifiers} if modifiers else {})})
    return {"documentKind": "html", "source": source, "contentHash": hashlib.sha256(source.encode()).hexdigest(),
            "repository": "sample", "path": f"g{index}/index.html", "sourceGroup": f"sample:g{index}",
            "result": {"offsetEncoding": "utf-16", "spans": spans, "regions": [], "modernExclusions": []}}


class DataTests(unittest.TestCase):
    def setUp(self):
        self.schema = Schema.load(REPOSITORY / "packs/html/model-schema.json")

    def test_unicode_masks_and_closing_modifier(self):
        doc = record()
        encoded = encode(doc, self.schema)
        self.assertEqual(bytes(list(encoded.columns["input_ids"])).decode(), doc["source"])
        offset = 0
        for character in doc["source"]:
            for continuation in range(1, len(character.encode())):
                self.assertEqual(encoded.columns["boundary_labels"][offset + continuation], IGNORE)
            offset += len(character.encode())
        at = doc["source"].encode().index(b"</p>") + 2
        self.assertEqual(encoded.columns["modifier_bits"][at], 1)

    def test_source_hash_surrogate_and_gap_checks(self):
        for mutation in ("hash", "surrogate", "gap"):
            doc = record()
            if mutation == "hash": doc["source"] += "x"
            elif mutation == "surrogate": doc["result"]["spans"][3]["end"] = 4
            else: doc["result"]["spans"].pop()
            with self.assertRaises(ValueError): encode(doc, self.schema)

    def test_non_gold_evaluation_cuts_and_group_isolation(self):
        source = "a" * 480 + "星" * 30 + "b" * 50
        doc = {"documentKind": "html", "source": source, "contentHash": hashlib.sha256(source.encode()).hexdigest(),
               "result": {"offsetEncoding": "utf-16", "spans": [
                   {"start": 0, "end": 480, "tokenType": "text"},
                   {"start": 480, "end": len(source), "tokenType": "comment"}]}}
        encoded = encode(doc, self.schema)
        fixed = windows(encoded, 512, False)[0]
        self.assertEqual(windows(encoded, 512, True)[0][0][1], 480)
        doc["result"]["spans"] = [{"start": 0, "end": len(source), "tokenType": "text"}]
        self.assertEqual(windows(encode(doc, self.schema), 512, False)[0], fixed)
        weights = {f"source:{index}": Counter(html=10+index) for index in range(12)}
        self.assertEqual(assign_groups(weights, 42), assign_groups(dict(reversed(list(weights.items()))), 42))
        self.assertEqual(set(assign_groups(weights, 42).values()), {"train", "validation", "test"})

    def test_immutable_preparation_excludes_cross_group_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "html"
            folder = root / "gold/input"
            folder.mkdir(parents=True)
            records = [record(index) for index in range(1, 13)]
            duplicate = copy.deepcopy(records[0])
            duplicate.update(repository="other", path="copy/index.html", sourceGroup="other:copy")
            records.append(duplicate)
            gold = folder / "labeled-sample.jsonl"
            gold.write_text("".join(json.dumps(doc) + "\n" for doc in records))
            manifest = {"format": "nsh-html-corpus-v1", "files": len(records),
                        "checksums": {gold.name: file_hash(gold)},
                        "provenance": {"schemaHash": file_hash(REPOSITORY / "packs/html/model-schema.json"),
                                       "semanticContractHash": file_hash(REPOSITORY / "packs/html/SEMANTICS.md")}}
            (folder / "sample.json").write_text(json.dumps(manifest))
            (root / "current-gold.json").write_text(json.dumps({"directory": "gold/input", "manifestHash": file_hash(folder / "sample.json")}))
            prepared = prepare(root)
            self.assertEqual(prepared["exactDuplicateRecords"], 1)
            self.assertEqual(prepared["excludedCopyDocuments"], 1)
            self.assertEqual(prepared["retainedDocuments"], 11)
            self.assertEqual(prepare(root), prepared)
            target = root / "prepared" / prepared["snapshot"] / "train/input_ids.bin"
            with target.open("r+b") as stream: stream.write(b"\0")
            with self.assertRaisesRegex(ValueError, "corrupt"): prepare(root)


if __name__ == "__main__": unittest.main()
