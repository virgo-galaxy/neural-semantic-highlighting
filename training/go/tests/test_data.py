from __future__ import annotations

from array import array
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

GO_TRAINING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GO_TRAINING))
from encoding import BEGIN, IGNORE, INSIDE, PAD, Schema, digest, encode, padded_window, repair_missing_tildes, windows
from dataset import GoWindowDataset
from prepare import Groups, build, dumps, focused_copy_exclusions, hash_split, verify_output

ROOT = GO_TRAINING.parents[1]
SCHEMA = Schema.load(ROOT / "packs/go/schema.json")


def make_record(source, spans, path="source.go", package="sample"):
    return {"package": package, "path": path, "documentKind": "go", "contentHash": digest(source.encode("utf-8")),
            "source": source, "result": {"offsetEncoding": "utf-16", "spans": spans}}


def span(start, end, role, modifiers=None):
    result = {"start": start, "end": end, "tokenType": role}
    if modifiers:
        result["modifiers"] = modifiers
    return result


class EncodingTests(unittest.TestCase):
    def test_all_existing_gold_fixtures_validate(self):
        for path in sorted((ROOT / "packs/go/fixtures").glob("*/expected.json")):
            with self.subTest(fixture=path.parent.name):
                expected = json.loads(path.read_text(encoding="utf-8"))
                raw = (path.parent / "source.go").read_bytes()
                source = raw.decode("utf-8")
                result = expected.get("result", expected)
                record = make_record(source, result["spans"])
                encoded = encode(record, SCHEMA)
                refs, _ = windows(encoded, 512, True)
                rebuilt = b"".join(bytes(list(encoded.columns["input_ids"][lo:hi])) for lo, hi in refs)
                self.assertEqual(rebuilt, raw)

    def test_unicode_continuation_masks_and_modifiers(self):
        source = '"\U0001f680"'
        record = make_record(source, [span(0, 4, "string", ["readonly"])])
        encoded = encode(record, SCHEMA)
        self.assertEqual(list(encoded.columns["input_ids"]), list(source.encode()))
        self.assertEqual(list(encoded.columns["boundary_labels"]), [BEGIN, INSIDE, IGNORE, IGNORE, IGNORE, INSIDE])
        bit = 1 << SCHEMA.modifiers.index("readonly")
        self.assertEqual(list(encoded.columns["modifier_bits"]), [bit, 0, 0, 0, 0, 0])

    def test_surrogate_middle_rejected(self):
        record = make_record('"\U0001f680"', [span(0, 2, "string")])
        with self.assertRaisesRegex(ValueError, "UTF-16"):
            encode(record, SCHEMA)

    def test_source_hash_rejected(self):
        record = make_record("abc", [span(0, 3, "variable")])
        record["contentHash"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            encode(record, SCHEMA)

    def test_unknown_roles_and_modifiers_rejected(self):
        for item in (span(0, 1, "unknown"), span(0, 1, "variable", ["not-a-modifier"])):
            with self.assertRaises(ValueError):
                encode(make_record("x", [item]), SCHEMA)

    def test_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            encode(make_record("hello", [span(0, 3, "variable"), span(2, 5, "string")]), SCHEMA)

    def test_unlabeled_identifier_is_not_outside_training(self):
        with self.assertRaisesRegex(ValueError, "Unlabeled non-whitespace"):
            encode(make_record("missing", []), SCHEMA)

    def test_crlf_bytes_are_preserved(self):
        record = make_record("// sample\r\n", [span(0, 9, "comment")])
        encoded = encode(record, SCHEMA)
        self.assertEqual(bytes(list(encoded.columns["input_ids"])), b"// sample\r\n")

    def test_adaptive_cursor_uses_span_boundary(self):
        record = make_record("aa bbbbb cc", [span(0, 2, "variable"), span(3, 8, "string"), span(9, 11, "variable")])
        encoded = encode(record, SCHEMA)
        refs, stats = windows(encoded, 6, True)
        self.assertEqual(refs, [(0, 3), (3, 9), (9, 11)])
        self.assertEqual(stats["spanCuts"], 1)

    def test_evaluation_never_uses_gold_cut(self):
        source = "aa bbbbb cc"
        a = encode(make_record(source, [span(0, len(source), "string")]), SCHEMA)
        b = encode(make_record(source, [span(0, 2, "variable"), span(3, 8, "string"), span(9, 11, "variable")]), SCHEMA)
        self.assertEqual(windows(a, 6, False)[0], windows(b, 6, False)[0])
        self.assertEqual(windows(a, 6, False)[0], [(0, 6), (6, 11)])

    def test_overlong_span_makes_progress_without_fake_begin(self):
        encoded = encode(make_record('"' + 'x'*20 + '"', [span(0, 22, "string")]), SCHEMA)
        refs, stats = windows(encoded, 8, True)
        self.assertEqual(refs, [(0, 8), (8, 16), (16, 22)])
        self.assertEqual(stats["insideStarts"], 2)
        self.assertEqual(padded_window(encoded, 8, 16, 8)["boundary_labels"][0], INSIDE)

    def test_unicode_cuts_do_not_split_characters(self):
        text = '"' + '\U0001f680'*4 + '"'
        encoded = encode(make_record(text, [span(0, 10, "string")]), SCHEMA)
        for adaptive in (True, False):
            refs, _ = windows(encoded, 8, adaptive)
            for lo, hi in refs:
                bytes(list(encoded.columns["input_ids"][lo:hi])).decode("utf-8")
                self.assertLessEqual(hi-lo, 8)
            self.assertEqual(refs[-1][1], len(text.encode()))

    def test_padding_is_ignored(self):
        encoded = encode(make_record("x", [span(0, 1, "variable")]), SCHEMA)
        row = padded_window(encoded, 0, 1, 8)
        self.assertEqual(list(row["input_ids"]), [ord("x")] + [PAD]*7)
        self.assertEqual(list(row["boundary_labels"]), [BEGIN] + [IGNORE]*7)

    def test_legacy_tilde_repair_is_audited_and_nonmutating(self):
        original = make_record("~int", [span(1, 4, "type", ["default-library"])])
        repaired, count = repair_missing_tildes(original)
        self.assertEqual(count, 1)
        self.assertEqual(len(original["result"]["spans"]), 1)
        self.assertEqual(repaired["result"]["spans"][0], span(0, 1, "operator"))
        self.assertEqual(repaired["goldRepairs"]["legacyMissingTildeOperators"], 1)
        encode(repaired, SCHEMA)
        self.assertEqual(repair_missing_tildes(repaired)[1], 0)

    def test_tilde_inside_existing_string_or_comment_not_repaired(self):
        for source, role in (("~", "string"), ("// ~", "comment")):
            record = make_record(source, [span(0, len(source), role)])
            self.assertEqual(repair_missing_tildes(record)[1], 0)

    def test_near_copy_fingerprints_preserve_literal_whitespace(self):
        a = encode(make_record('"a b"', [span(0, 5, "string")]), SCHEMA)
        b = encode(make_record('"ab"', [span(0, 4, "string")]), SCHEMA)
        self.assertNotEqual(a.normalized_hash, b.normalized_hash)
        self.assertEqual(a.shape_hash, b.shape_hash)


class BuilderTests(unittest.TestCase):
    def fixture_corpus(self, root, *, duplicate=False, conflict=False, gap=False):
        folder = root / "curricula/test"
        folder.mkdir(parents=True)
        records = []
        # Distinct structures keep each independent family in its explicit split.
        sources = [("train", "word", [span(0, 4, "variable")]),
                   ("validation", "[12]", [span(0, 1, "punctuation"), span(1, 3, "number"), span(3, 4, "punctuation")]),
                   ("test", "/* note */", [span(0, 10, "comment")])]
        for split, source, spans in sources:
            record = make_record(source, spans, path=split + ".go")
            record.update(family="family-"+split, features=["test-feature"], since="1.18", variant=0, split=split)
            records.append(record)
        if duplicate:
            record = copy.deepcopy(records[0]); record["path"] = "duplicate.go"
            if conflict:
                record["result"]["spans"][0]["tokenType"] = "parameter"
            records.append(record)
        if gap:
            record = make_record("unresolved", [], path="gap.go")
            record.update(family="family-train", features=[], since="1.18", variant=1, split="train")
            records.append(record)
        self.write_corpus(folder, records)
        config = root / "config.json"
        config.write_text(dumps({"formatVersion": 1, "sources": [{"id": "test", "kind": "focused", "directory": "curricula/test"}]}))
        return folder, config

    def write_corpus(self, folder, records):
        manifest = {"formatVersion": 1, "corpus": "test", "toolchain": "go1.27.1", "kind": "focused",
                    "files": [{"package": r["package"], "path": r["path"], "contentHash": r["contentHash"], "size": len(r["source"].encode())} for r in records]}
        (folder / "sample.json").write_text(dumps(manifest))
        (folder / "labeled-sample.jsonl").write_text("".join(dumps(r)+"\n" for r in records))

    def run_build(self, root, config):
        with contextlib.redirect_stdout(io.StringIO()):
            return build(root, config, root / "prepared")

    def test_end_to_end_replay_and_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder, config = self.fixture_corpus(root, duplicate=True)
            report = self.run_build(root, config)
            self.assertEqual(report["inputCounts"]["exactDuplicatesRemoved"], 1)
            directory = root / "prepared" / report["snapshot"][:20]
            verify_output(directory, report)
            groups = []
            for split in ("train", "validation", "test"):
                row = json.loads((directory / split / "documents.jsonl").read_text())
                groups.append(row["groupId"])
                with GoWindowDataset(directory, split) as dataset:
                    self.assertEqual(len(dataset), 1)
                    self.assertEqual(len(dataset[0]["input_ids"]), 512)
                    self.assertEqual(sum(dataset[0]["attention_mask"]), len(row["source"].encode()))
                    with self.assertRaises(IndexError):
                        dataset[1]
            self.assertEqual(len(set(groups)), 3)
            self.assertEqual(self.run_build(root, config), report)
            self.assertTrue((folder / "labeled-sample.jsonl").exists())
            self.assertFalse((root / "prepared/.prepare.lock").exists())

    def test_conflicting_gold_aborts_without_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, config = self.fixture_corpus(root, duplicate=True, conflict=True)
            with self.assertRaisesRegex(ValueError, "conflicting Gold"):
                self.run_build(root, config)
            self.assertFalse((root / "prepared/current.json").exists())

    def test_incomplete_gold_is_quarantined_not_taught(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, config = self.fixture_corpus(root, gap=True)
            report = self.run_build(root, config)
            self.assertEqual(report["inputCounts"]["quarantinedDocuments"], 1)
            directory = root / "prepared" / report["snapshot"][:20]
            self.assertEqual(len((directory / "quarantine.jsonl").read_text().splitlines()), 1)
            self.assertEqual(sum(s["documents"] for s in report["splits"].values()), 3)

    def test_near_copy_across_forced_splits_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder, config = self.fixture_corpus(root)
            rows = [json.loads(x) for x in (folder / "labeled-sample.jsonl").read_text().splitlines()]
            rows[1].update(source="name", contentHash=digest(b"name"), result={"offsetEncoding":"utf-16", "spans":[span(0,4,"variable")]})
            self.write_corpus(folder, rows)
            with self.assertRaisesRegex(ValueError, "split conflict"):
                self.run_build(root, config)

    def test_targeted_mined_copy_conflict_prefers_heldout(self):
        copies = Groups()
        copies.union("real", "heldout")
        hints = {"family:real": {"train"}, "family:heldout": {"validation"}}
        provenance = {
            "real": [{"corpus": "targeted", "package": "real", "path": "real.go", "group": "family:real",
                      "split": "train", "focusedGenerator": "targeted-go-feature-miner-v1"}],
            "heldout": [{"corpus": "synthetic", "package": "sample", "path": "validation.go", "group": "family:heldout",
                         "split": "validation", "focusedGenerator": "modern-go-focused-v2"}],
        }
        origins, documents = focused_copy_exclusions(provenance, hints, copies)
        self.assertEqual(documents, {"real"})
        self.assertEqual(len(origins), 1)
        self.assertEqual(origins[0]["reason"], "targeted-train-near-heldout-focused-copy")

    def test_synthetic_copy_conflict_still_fails(self):
        copies = Groups()
        copies.union("train", "heldout")
        hints = {"family:train": {"train"}, "family:heldout": {"validation"}}
        provenance = {
            "train": [{"corpus": "synthetic", "package": "sample", "path": "train.go", "group": "family:train",
                       "split": "train", "focusedGenerator": "modern-go-focused-v2"}],
            "heldout": [{"corpus": "synthetic", "package": "sample", "path": "validation.go", "group": "family:heldout",
                         "split": "validation", "focusedGenerator": "modern-go-focused-v2"}],
        }
        with self.assertRaisesRegex(ValueError, "split conflict"):
            focused_copy_exclusions(provenance, hints, copies)

    def test_targeted_real_train_near_heldout_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthetic = root / "curricula/synthetic"
            targeted = root / "curricula/targeted"
            synthetic.mkdir(parents=True); targeted.mkdir(parents=True)

            train_seed = make_record(
                "[12]",
                [span(0, 1, "punctuation"), span(1, 3, "number"), span(3, 4, "punctuation")],
                path="train.go",
            )
            train_seed.update(family="train-family", features=["baseline"], since="1.18", variant=0, split="train")
            heldout = make_record("name", [span(0, 4, "variable")], path="validation.go")
            heldout.update(family="validation-family", features=["generic-method"], since="1.27", variant=0, split="validation")
            test_seed = make_record("/* note */", [span(0, 10, "comment")], path="test.go")
            test_seed.update(family="test-family", features=["baseline"], since="1.18", variant=0, split="test")
            train = make_record("other", [span(0, 5, "variable")], path="real.go", package="real")
            train.update(family="targeted-real/module/pkg", features=["generic-method"], since="1.27", variant=0, split="train")

            def write(folder, corpus, records, generator):
                manifest = {"formatVersion": 1, "corpus": corpus, "toolchain": "go1.27.1", "kind": "focused",
                            "generator": generator,
                            "files": [{"package": r["package"], "path": r["path"], "contentHash": r["contentHash"],
                                       "size": len(r["source"].encode())} for r in records]}
                (folder / "sample.json").write_text(dumps(manifest))
                (folder / "labeled-sample.jsonl").write_text("".join(dumps(r)+"\n" for r in records))

            write(synthetic, "synthetic", [train_seed, heldout, test_seed], "modern-go-focused-v2")
            write(targeted, "targeted", [train], "targeted-go-feature-miner-v1")
            config = root / "config.json"
            config.write_text(dumps({"formatVersion": 1, "sources": [
                {"id": "synthetic", "kind": "focused", "directory": "curricula/synthetic"},
                {"id": "targeted", "kind": "focused", "directory": "curricula/targeted"},
            ]}))

            report = self.run_build(root, config)
            self.assertEqual(report["inputCounts"]["heldoutNearCopyDocumentsExcluded"], 1)
            self.assertEqual(report["inputCounts"]["heldoutNearCopyOriginsExcluded"], 1)
            directory = root / "prepared" / report["snapshot"][:20]
            rows = [json.loads(line) for line in (directory / "validation/documents.jsonl").read_text().splitlines()]
            self.assertEqual([row["path"] for row in rows], ["validation.go"])
            exclusions = [json.loads(line) for line in (directory / "focused-near-copy-exclusions.jsonl").read_text().splitlines()]
            self.assertEqual(exclusions[0]["corpus"], "targeted")
            self.assertEqual(exclusions[0]["reason"], "targeted-train-near-heldout-focused-copy")

    def test_manifest_missing_record_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder, config = self.fixture_corpus(root)
            path = folder / "labeled-sample.jsonl"
            path.write_text("\n".join(path.read_text().splitlines()[:-1])+"\n")
            with self.assertRaisesRegex(ValueError, "Incomplete JSONL"):
                self.run_build(root, config)

    def test_missing_corpus_does_not_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder, config = self.fixture_corpus(root)
            (folder / "sample.json").unlink()
            with self.assertRaisesRegex(ValueError, "Missing corpus"):
                self.run_build(root, config)

    def test_corrupt_binary_snapshot_detected_on_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, config = self.fixture_corpus(root)
            report = self.run_build(root, config)
            column = root / "prepared" / report["snapshot"][:20] / "train/input_ids.bin"
            column.write_bytes(b"bad")
            with self.assertRaisesRegex(ValueError, "Corrupted"):
                self.run_build(root, config)

    def test_wrong_toolchain_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder, config = self.fixture_corpus(root)
            manifest = json.loads((folder / "sample.json").read_text()); manifest["toolchain"] = "go1.18"
            (folder / "sample.json").write_text(dumps(manifest))
            with self.assertRaisesRegex(ValueError, "toolchain"):
                self.run_build(root, config)

    def test_union_and_split_determinism(self):
        groups = Groups()
        groups.union("module:b", "module:a")
        groups.union("module:c", "module:b")
        self.assertEqual(groups.find("module:c"), "module:a")
        self.assertEqual(hash_split(groups.find("module:c"), 1729), hash_split(groups.find("module:a"), 1729))


if __name__ == "__main__":
    unittest.main()
