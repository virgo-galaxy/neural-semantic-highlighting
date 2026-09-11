from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare import build, dumps, source_group
from repair import SyntaxRepairer, apply_type_switch_declarations
from splitting import assign_groups, natural_balance
import test_data
from test_data import ROOT, SCHEMA, make_record, span
from encoding import encode


class SyntaxRepairTests(unittest.TestCase):
    def test_repair_is_nonmutating_idempotent_and_preserves_prior_audit(self):
        record = make_record("switch v", [span(0, 6, "keyword")])
        record["goldRepairs"] = {"legacyMissingTildeOperators": 1}
        original = copy.deepcopy(record)
        candidates = [span(7, 8, "variable", ["declaration"])]
        updated, count = apply_type_switch_declarations(record, candidates)
        self.assertEqual(count, 1)
        self.assertEqual(record, original)
        self.assertEqual(updated["goldRepairs"], {"legacyMissingTildeOperators": 1, "legacyTypeSwitchDeclarations": 1})
        encode(updated, SCHEMA)
        self.assertEqual(apply_type_switch_declarations(updated, candidates)[1], 0)

    def test_other_unresolved_names_stay_incomplete(self):
        record = make_record("switch v missing", [span(0, 6, "keyword")])
        updated, count = apply_type_switch_declarations(record, [span(7, 8, "variable", ["declaration"])])
        self.assertEqual(count, 1)
        with self.assertRaisesRegex(ValueError, "Unlabeled non-whitespace"):
            encode(updated, SCHEMA)

    def test_existing_conflicting_labels_are_not_overwritten(self):
        record = make_record("switch v", [span(0, 6, "keyword"), span(7, 8, "type")])
        with self.assertRaisesRegex(ValueError, "conflicts"):
            apply_type_switch_declarations(record, [span(7, 8, "variable", ["declaration"])])
        self.assertEqual(record["result"]["spans"][-1]["tokenType"], "type")

    def test_duplicate_candidates_are_counted_once(self):
        record = make_record("switch v", [span(0, 6, "keyword")])
        candidate = span(7, 8, "variable", ["declaration"])
        self.assertEqual(apply_type_switch_declarations(record, [candidate, candidate])[1], 1)

    def test_invalid_candidate_rejected(self):
        record = make_record("v", [])
        for candidate in [span(-1, 1, "variable", ["declaration"]), span(0, 2, "variable", ["declaration"]), span(0, 1, "type")]:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                apply_type_switch_declarations(record, [candidate])

    def test_no_switch_does_not_start_go_process(self):
        with SyntaxRepairer(ROOT, "go1.27.1") as repairer, patch.object(repairer, "_start", side_effect=AssertionError("unexpected Go process")):
            self.assertEqual(repairer.repair(make_record("unresolved", []))[1], 0)

    def test_protocol_candidates_not_regex_determine_repair(self):
        record = make_record('"switch fake := x.(type)" missing', [span(0, 24, "string")])
        with SyntaxRepairer(ROOT, "go1.27.1") as repairer, patch.object(repairer, "declarations", return_value=[]) as request:
            updated, count = repairer.repair(record)
            self.assertEqual(count, 0)
            self.assertIs(updated, record)
            request.assert_called_once_with(record["source"])


class BalancedSplitTests(unittest.TestCase):
    def test_weighted_assignment_is_order_independent(self):
        weights = {f"module:example.test/{i}": weight for i, weight in enumerate([500, 160, 100, 80, 60, 30, 20, 10])}
        a = assign_groups(weights, 17)
        b = assign_groups(dict(reversed(list(weights.items()))), 17)
        self.assertEqual(a, b)
        loads = {split: sum(weights[g] for g in weights if a[g] == split) for split in ("train", "validation", "test")}
        self.assertTrue(natural_balance(loads)["passed"])

    def test_equal_independent_groups_are_balanced(self):
        result = assign_groups({f"group:{i}": 1 for i in range(20)}, 1729)
        self.assertEqual({s: list(result.values()).count(s) for s in ("train", "validation", "test")},
                         {"train": 16, "validation": 2, "test": 2})

    def test_too_few_groups_is_not_disguised_as_evaluation(self):
        with self.assertRaisesRegex(ValueError, "at least three"):
            assign_groups({"a": 100, "b": 1}, 1)

    def test_natural_quality_gate_cannot_be_filled_by_focus(self):
        with self.assertRaisesRegex(ValueError, "balance gate failed"):
            natural_balance({"train": 9900, "validation": 50, "test": 50})

    def test_indivisible_oversized_group_is_not_split(self):
        weights = {"large": 9900, "a": 50, "b": 50}
        assigned = assign_groups(weights, 1)
        loads = {s: sum(weights[g] for g in weights if assigned[g] == s) for s in ("train", "validation", "test")}
        self.assertEqual(len(assigned), 3)
        with self.assertRaisesRegex(ValueError, "balance gate"):
            natural_balance(loads)

    def test_module_and_subsystem_boundaries_are_preserved(self):
        self.assertEqual(source_group({"kind": "module"}, {"source": {"module": "example.test/library"}},
                                      {"package": "example.test/library/sub"}), "module:example.test/library")
        self.assertEqual(source_group({"kind": "stdlib"}, {}, {"package": "net/http"}), "stdlib:net")
        self.assertEqual(source_group({"kind": "stdlib"}, {}, {"package": "internal/runtime/maps"}), "stdlib:internal/runtime")


def natural_record(count: int, path: str) -> dict:
    # A deliberately small, valid Go subset with independently specified labels.
    tokens = [("package", "keyword", []), ("sample", "namespace", ["declaration"]),
              ("const", "keyword", []), ("Value", "variable", ["declaration", "readonly"]), ("=", "operator", []), ("1", "number", [])]
    for _ in range(count):
        tokens.extend([("+", "operator", []), ("1", "number", [])])
    source, spans = "", []
    for index, (text, role, modifiers) in enumerate(tokens):
        if index:
            source += "\n" if index == 2 else " "
        start = len(source)
        source += text
        spans.append(span(start, len(source), role, modifiers))
    source += "\n"
    return make_record(source, spans, path=path)


class SourceIsolationRegressionTests(unittest.TestCase):
    def make_inventory(self, root: Path, *, copies=True):
        specs = []
        for index in range(20):
            name = f"source-{index:02d}"
            module = f"example.test/{name}"
            folder = root / "corpora" / name
            folder.mkdir(parents=True)
            records = [natural_record(index + 2, "source.go")]
            if copies:
                records.append(natural_record(0, "shared.go"))
            for record in records:
                record["package"] = module
            manifest = {"formatVersion": 2, "corpus": name, "toolchain": "go1.27.1", "source": {"module": module},
                        "files": [{"package": r["package"], "path": r["path"], "contentHash": r["contentHash"], "size": len(r["source"].encode())} for r in records]}
            (folder / "sample.json").write_text(dumps(manifest))
            (folder / "labeled-sample.jsonl").write_text("".join(dumps(r)+"\n" for r in records))
            specs.append({"id": name, "kind": "module", "module": module, "directory": f"corpora/{name}"})
        config = root / "config.json"
        config.write_text(dumps({"formatVersion": 1, "sources": specs}))
        return config

    def test_shared_copy_does_not_fuse_twenty_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_inventory(root)
            helper = test_data.BuilderTests()
            report = helper.run_build(root, config)
            self.assertEqual(report["inputCounts"]["exactDuplicatesRemoved"], 19)
            self.assertEqual(report["inputCounts"]["crossGroupCopyDocumentsExcluded"], 1)
            self.assertTrue(report["qualityGates"]["naturalSplitBalance"]["passed"])
            folder = root / "prepared" / report["snapshot"][:20]
            grouped = json.loads((folder / "split-groups.json").read_text())
            self.assertEqual(len(grouped), 20)
            self.assertEqual(sum(row["documents"] for row in grouped), 20)
            excluded = json.loads((folder / "cross-group-copies.jsonl").read_text())
            self.assertEqual(len(excluded["provenance"]), 20)
            source_splits = {}
            shapes = {}
            for split in ("train", "validation", "test"):
                for line in (folder / split / "documents.jsonl").read_text().splitlines():
                    record = json.loads(line)
                    self.assertNotEqual(record["id"], excluded["documentId"])
                    for origin in record["provenance"]:
                        old = source_splits.setdefault(origin["group"], split)
                        self.assertEqual(old, split)
                    fingerprint = encode(record, SCHEMA).shape_hash
                    self.assertEqual(shapes.setdefault(fingerprint, split), split)
            self.assertEqual(helper.run_build(root, config), report)
            self.assertTrue((root / "corpora/source-00/labeled-sample.jsonl").is_file())

    def test_alpha_renamed_cross_module_copies_are_excluded_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.make_inventory(root)
            path = root / "corpora/source-01/labeled-sample.jsonl"
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            copy_record = rows[1]
            copy_record["source"] = copy_record["source"].replace("Value", "Other")
            from encoding import digest
            copy_record["contentHash"] = digest(copy_record["source"].encode())
            path.write_text("".join(dumps(row)+"\n" for row in rows))
            manifest_path = path.parent / "sample.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"][1]["contentHash"] = copy_record["contentHash"]
            manifest_path.write_text(dumps(manifest))
            report = test_data.BuilderTests().run_build(root, config)
            self.assertEqual(report["inputCounts"]["crossGroupCopyDocumentsExcluded"], 2)
            self.assertEqual(sum(row["documents"] for row in report["splits"].values()), 20)

    def test_infeasible_natural_balance_does_not_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = self.make_inventory(root, copies=False)
            with patch("prepare.natural_balance", side_effect=ValueError("balance gate failed")):
                with self.assertRaisesRegex(ValueError, "balance gate"):
                    test_data.BuilderTests().run_build(root, config)
            self.assertFalse((root / "prepared/current.json").exists())
            self.assertFalse((root / "prepared/.prepare.lock").exists())

    def test_parser_recovery_then_encode_preserves_remaining_gap_quarantine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); helper = test_data.BuilderTests()
            folder, config = helper.fixture_corpus(root)
            rows = [json.loads(line) for line in (folder / "labeled-sample.jsonl").read_text().splitlines()]
            for index, tail in enumerate(("", " unresolved")):
                row = make_record("switch v"+tail, [span(0, 6, "keyword")], path=f"guard-{index}.go")
                row.update(family="family-train", features=[], since="1.18", variant=index+1, split="train")
                rows.append(row)
            helper.write_corpus(folder, rows)
            with patch.object(SyntaxRepairer, "declarations", return_value=[span(7, 8, "variable", ["declaration"])]):
                report = helper.run_build(root, config)
            self.assertEqual(report["inputCounts"]["repairedTypeSwitchDeclarations"], 2)
            self.assertEqual(report["inputCounts"]["recoveredTypeSwitchDocuments"], 1)
            self.assertEqual(report["inputCounts"]["quarantinedDocuments"], 1)
            self.assertEqual(sum(row["documents"] for row in report["splits"].values()), 4)


if __name__ == "__main__":
    unittest.main()
