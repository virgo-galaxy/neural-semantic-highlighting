"""Small CPU-only regressions; these fixtures are not model training corpora."""
from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checkpoints import load_checkpoint, model_from_checkpoint, save_checkpoint, select_device, training_lock
from encoding import COLUMNS, IGNORE, PAD, Schema, digest, encode, little_endian_bytes, padded_window, windows
from inference import character_map, decode, document_logits, predicted_cut
from losses import compute_loss
from metrics import SpanMetrics, evaluate_fixed, evaluation_indices
from model import GoSemanticTransformer, ModelConfig, ModelOutput, parameter_count
from train import parser, run
from trainer_data import Snapshot, WindowSplit, epoch_batches, sha256_file, training_weights

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = Schema.load(ROOT / "packs/go/schema.json")
SCHEMA_DICT = {"tokenTypes": list(SCHEMA.token_types), "modifiers": list(SCHEMA.modifiers)}
CPU = torch.device("cpu")


def record(source: str, spans: list[dict], stream: str, name: str) -> dict:
    return {"source": source, "result": {"offsetEncoding": "utf-16", "spans": spans},
            "contentHash": digest(source.encode()), "id": digest((name + source).encode()),
            "documentKind": "go", "stream": stream, "features": ["test-syntax"] if stream == "focus" else [],
            "groupId": name, "path": name + ".go", "package": "sample"}


def synthetic_snapshot(folder: Path) -> Path:
    folder.mkdir(parents=True)
    manifest = {"format": "nsh-go-byte-dataset-v1", "snapshot": "unit-test-snapshot", "contextBytes": 512,
                "schema": SCHEMA_DICT, "columns": {}, "splits": {},
                "labels": {"padByteId": PAD, "ignoreId": IGNORE, "boundaryClasses": ["outside", "begin", "inside"],
                           "modifierSupervision": "span-beginnings", "continuationBytes": "ignored"},
                "policy": {"evaluationWindowing": "character-safe-fixed-cursor", "split": "size-balanced-source-groups-before-windowing"},
                "qualityGates": {"naturalSplitBalance": {"applicable": True, "passed": True}}}
    for split in ("train", "validation", "test"):
        path = folder / split
        path.mkdir()
        documents, refs = [], []
        binary = {name: bytearray() for name in COLUMNS}
        # A long, single span deliberately crosses fixed validation window cuts.
        texts = [("natural", "x", [{"start": 0, "end": 1, "tokenType": "variable", "modifiers": ["declaration"]}]),
                 ("natural", '"' + "z" * 600 + '"', [{"start": 0, "end": 602, "tokenType": "string"}]),
                 ("focus", '"\U0001f680"\r\n', [{"start": 0, "end": 4, "tokenType": "string"}])]
        for number, (stream, source, spans) in enumerate(texts):
            doc = record(source, spans, stream, split + str(number))
            encoded = encode(doc, SCHEMA)
            for start, end in windows(encoded, 512, split == "train")[0]:
                row = padded_window(encoded, start, end, 512)
                for name, values in row.items():
                    binary[name] += little_endian_bytes(values)
                refs.append({"documentId": doc["id"], "groupId": doc["groupId"], "stream": stream,
                             "startByte": start, "endByte": end, "length": end - start})
            documents.append(doc)
        (path / "documents.jsonl").write_text("".join(json.dumps(d) + "\n" for d in documents), encoding="utf-8")
        (path / "windows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in refs), encoding="utf-8")
        for name, data in binary.items():
            (path / (name + ".bin")).write_bytes(data)
        manifest["splits"][split] = {"windows": len(refs), "documents": len(documents),
                                     "naturalWindows": sum(r["stream"] == "natural" for r in refs),
                                     "focusWindows": sum(r["stream"] == "focus" for r in refs)}
    manifest["checksums"] = {str(p.relative_to(folder)): sha256_file(p) for p in folder.rglob("*") if p.is_file()}
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


class TrainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.threads)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.snapshot = Snapshot.open(synthetic_snapshot(self.folder / "snapshot"))

    def split(self, name="train"):
        result = WindowSplit(self.snapshot, name)
        self.addCleanup(result.close)
        return result

    def options(self, output, epochs=1):
        return parser().parse_args(["--snapshot", str(self.snapshot.path), "--output-dir", str(output),
                                    "--smoke", "--epochs", str(epochs), "--device", "cpu", "--cpu-threads", "1",
                                    "--batch-size", "2", "--focus-batch-size", "2", "--focus-every", "1",
                                    "--smoke-main-batches", "2", "--smoke-eval-windows", "8"])

    def tiny_model(self):
        return ModelConfig(width=16, heads=2, layers=1, feed_forward=32, dropout=.1)

    def test_model_uses_go_head_counts(self):
        model = GoSemanticTransformer(ModelConfig(), 16, 3)
        self.assertEqual(parameter_count(model), 894614)
        output = model(torch.tensor([[12, 15]]), torch.tensor([[True, True]]))
        self.assertEqual(output.boundary.shape, (1, 2, 3))
        self.assertEqual(output.token_type.shape, (1, 2, 16))
        self.assertEqual(output.modifier.shape, (1, 2, 3))
        self.assertFalse(torch.equal(model.layers[0].linear1.weight, model.layers[1].linear1.weight))

    def test_context_and_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            GoSemanticTransformer(ModelConfig(width=17, heads=4), 16, 3)
        model = GoSemanticTransformer(self.tiny_model(), 16, 3)
        with self.assertRaises(ValueError):
            model(torch.zeros((1, 513), dtype=torch.long), torch.ones((1, 513), dtype=torch.bool))

    def test_schema_mismatch_rejected(self):
        manifest = copy.deepcopy(self.snapshot.manifest)
        manifest["schema"]["tokenTypes"].reverse()
        (self.snapshot.path / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "schema"):
            Snapshot.open(self.snapshot.path)

    def test_mutated_column_rejected_before_training(self):
        path = self.snapshot.path / "train/input_ids.bin"
        data = bytearray(path.read_bytes()); data[0] ^= 1
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "checksum"):
            WindowSplit(self.snapshot, "train")

    def test_batches_cover_natural_once_and_only_train_focus(self):
        split = self.split()
        plan = epoch_batches(split, batch_size=2, focus_batch_size=2, focus_every=1, seed=42, epoch=1)
        natural = [i for k, ids in plan if k == "natural" for i in ids]
        focus = [i for k, ids in plan if k == "focus" for i in ids]
        self.assertCountEqual(natural, split.streams["natural"])
        self.assertEqual(len(natural), len(set(natural)))
        self.assertTrue(set(focus).issubset(split.streams["focus"]))
        self.assertEqual(len(focus), 4)
        self.assertEqual(plan, epoch_batches(split, batch_size=2, focus_batch_size=2, focus_every=1, seed=42, epoch=1))

    def test_heldout_labels_cannot_build_weights(self):
        with self.assertRaisesRegex(ValueError, "held-out"):
            training_weights(self.split("validation"))

    def test_mmap_tensor_bridge_preserves_masks_and_trims_padding(self):
        split = self.split()
        index = split.streams["focus"][0]
        batch = split.batch([index], CPU)
        self.assertEqual(batch["input_ids"].shape[1], 8)
        self.assertEqual(batch["boundary_labels"][0].tolist(), [1, 2, IGNORE, IGNORE, IGNORE, 2, 0, 0])
        self.assertTrue(batch["attention_mask"].all())

    def test_modifier_loss_ignores_inside_continuation_and_padding(self):
        batch = {"boundary_labels": torch.tensor([[1, 2, IGNORE, IGNORE]]),
                 "token_type_labels": torch.tensor([[0, 0, IGNORE, IGNORE]]),
                 "modifier_targets": torch.zeros((1, 4, 3))}
        out = ModelOutput(torch.zeros((1, 4, 3), requires_grad=True), torch.zeros((1, 4, 16), requires_grad=True),
                          torch.zeros((1, 4, 3), requires_grad=True))
        weights = {"boundary": torch.ones(3), "token_type": torch.ones(16), "modifier": torch.ones(3)}
        loss, _ = compute_loss(out, batch, weights)
        loss.backward()
        self.assertTrue(bool((out.modifier.grad[0, 1:] == 0).all()))
        self.assertTrue(bool((out.boundary.grad[0, 2:] == 0).all()))
        self.assertTrue(bool((out.token_type.grad[0, 2:] == 0).all()))
        changed = {**batch, "modifier_targets": batch["modifier_targets"].clone()}
        changed["modifier_targets"][0, 1:] = 1
        self.assertEqual(float(loss.detach()), float(compute_loss(out, changed, weights)[0].detach()))

    def test_no_semantic_or_begin_positions_has_finite_loss(self):
        batch = {"boundary_labels": torch.tensor([[0, IGNORE]]), "token_type_labels": torch.tensor([[IGNORE, IGNORE]]),
                 "modifier_targets": torch.zeros(1, 2, 3)}
        out = ModelOutput(torch.zeros(1, 2, 3, requires_grad=True), torch.zeros(1, 2, 16, requires_grad=True),
                          torch.zeros(1, 2, 3, requires_grad=True))
        weights = {"boundary": torch.ones(3), "token_type": torch.ones(16), "modifier": torch.ones(3)}
        loss, _ = compute_loss(out, batch, weights)
        self.assertTrue(bool(torch.isfinite(loss)))
        loss.backward()

    def test_cut_moves_to_predicted_begin_not_inside_unicode(self):
        boundary = torch.zeros(10, 3)
        boundary[:, 2] = 10
        boundary[4, 1] = 20
        self.assertEqual(predicted_cut(boundary, 8, [0, 1, 4, 5, 8, 9, 10]), 4)
        boundary[4, 1] = 0
        boundary[0, 1] = 20
        self.assertEqual(predicted_cut(boundary, 8, [0, 1, 4, 5, 8, 9, 10]), 8)

    def test_unicode_offsets_and_empty_decoder(self):
        source = '"\U0001f680"\r\n'
        encoded = encode(record(source, [{"start": 0, "end": 4, "tokenType": "string"}], "focus", "unicode"), SCHEMA)
        output = self.oracle_output(encoded)
        result = decode(source, output, SCHEMA_DICT)
        self.assertEqual(result, {"offsetEncoding": "utf-16", "spans": [{"start": 0, "end": 4, "tokenType": "string"}]})
        empty = ModelOutput(torch.empty(0, 3), torch.empty(0, 16), torch.empty(0, 3))
        self.assertEqual(decode("", empty, SCHEMA_DICT)["spans"], [])

    @staticmethod
    def oracle_output(encoded):
        length = len(encoded.columns["input_ids"])
        output = ModelOutput(torch.full((length, 3), -10.), torch.full((length, 16), -10.), torch.full((length, 3), -10.))
        for index in range(length):
            boundary, role = encoded.columns["boundary_labels"][index], encoded.columns["token_type_labels"][index]
            if boundary != IGNORE:
                output.boundary[index, boundary] = 10
            if role != IGNORE:
                output.token_type[index, role] = 10
            for bit in range(3):
                if encoded.columns["modifier_bits"][index] & (1 << bit):
                    output.modifier[index, bit] = 10
        return output

    def test_fixed_evaluation_reassembles_crossing_span_before_scoring(self):
        split = self.split("validation")
        docs = split.documents()
        all_logits = {name: self.oracle_output(encode(doc, SCHEMA)) for name, doc in docs.items()}
        class Oracle:
            def __init__(self): self.index = 0
            def eval(self): return self
            def __call__(self, ids, mask):
                batch, length = ids.shape
                out = ModelOutput(torch.full((batch, length, 3), -10.), torch.full((batch, length, 16), -10.), torch.full((batch, length, 3), -10.))
                for row in range(batch):
                    ref = split.refs[self.index]; self.index += 1
                    expected = all_logits[ref["documentId"]]
                    for output, gold in ((out.boundary, expected.boundary), (out.token_type, expected.token_type), (out.modifier, expected.modifier)):
                        output[row, :ref["length"]] = gold[ref["startByte"]:ref["endByte"]]
                return out
        report = evaluate_fixed(Oracle(), split, CPU, batch_size=2, log_every=0)
        self.assertEqual(report["streams"]["natural"]["exactSpan"]["f1"], 1)
        self.assertEqual(report["streams"]["natural"]["exactSpan"]["support"], 2)
        self.assertEqual(report["streams"]["focus"]["exactSpanIncludingModifiers"]["f1"], 1)
        self.assertEqual(report["focusFeatures"]["test-syntax"]["exactSpan"]["f1"], 1)

    def test_smoke_validation_keeps_documents_whole(self):
        split = self.split("validation")
        selected = set(evaluation_indices(split, 2))
        for indices in split.document_indices.values():
            self.assertIn(len(selected.intersection(indices)), (0, len(indices)))

    def test_span_metrics_count_wrong_type_and_modifiers_separately(self):
        metrics = SpanMetrics(SCHEMA_DICT)
        metrics.add({"spans": [{"start": 0, "end": 1, "tokenType": "variable", "modifiers": ["declaration"]}]},
                    {"spans": [{"start": 0, "end": 1, "tokenType": "variable"}]})
        report = metrics.report()
        self.assertEqual(report["exactSpan"]["f1"], 1)
        self.assertEqual(report["exactSpanIncludingModifiers"]["f1"], 0)

    def test_atomic_checkpoint_rejects_typescript_format(self):
        path = self.folder / "wrong.pt"
        save_checkpoint(path, {"format": "nsh-typescript-checkpoint"})
        with self.assertRaisesRegex(ValueError, "compatible Go"):
            load_checkpoint(path)

    def test_training_lock_rejects_concurrent_run_and_cleans_on_error(self):
        with self.assertRaisesRegex(RuntimeError, "failure"):
            with training_lock(self.folder):
                with self.assertRaisesRegex(ValueError, "lock exists"):
                    with training_lock(self.folder): pass
                raise RuntimeError("failure")
        self.assertFalse((self.folder / ".training.lock").exists())

    def test_smoke_train_reload_resume_does_not_open_test_data(self):
        # Deliberately corrupt held-out test bytes; training must not read them.
        (self.snapshot.path / "test/input_ids.bin").write_bytes(b"not-used-during-training")
        output = self.folder / "smoke"
        with contextlib.redirect_stdout(io.StringIO()):
            run(self.options(output), model_config=self.tiny_model())
        checkpoint = load_checkpoint(output / "last.pt")
        self.assertEqual(checkpoint["epoch"], 1)
        self.assertGreater(checkpoint["trainingState"]["optimizerSteps"], 0)
        self.assertTrue((output / "best.pt").exists())
        self.assertEqual(json.loads((output / "smoke-report.json").read_text())["checkpointReload"], "passed")
        args = parser().parse_args(["--resume", str(output / "last.pt"), "--epochs", "1", "--device", "cpu", "--cpu-threads", "1"])
        with contextlib.redirect_stdout(io.StringIO()):
            run(args)
        resumed = load_checkpoint(output / "last.pt")
        self.assertEqual(resumed["epoch"], 2)
        self.assertEqual(resumed["trainingState"]["optimizerSteps"], 2 * checkpoint["trainingState"]["optimizerSteps"])
        self.assertFalse((output / ".training.lock").exists())

    def test_resume_replays_uninterrupted_cpu_training(self):
        continuous, resumed = self.folder / "continuous", self.folder / "resumed"
        with contextlib.redirect_stdout(io.StringIO()):
            run(self.options(continuous, epochs=2), model_config=self.tiny_model())
            run(self.options(resumed), model_config=self.tiny_model())
            args = parser().parse_args(["--resume", str(resumed / "last.pt"), "--epochs", "1", "--device", "cpu", "--cpu-threads", "1"])
            run(args)
        a, b = load_checkpoint(continuous / "last.pt"), load_checkpoint(resumed / "last.pt")
        for key in a["model"]:
            torch.testing.assert_close(a["model"][key], b["model"][key], atol=0, rtol=0)

    def test_existing_output_and_mismatched_resume_refused(self):
        output = self.folder / "run"
        with contextlib.redirect_stdout(io.StringIO()):
            run(self.options(output), model_config=self.tiny_model())
            with self.assertRaisesRegex(ValueError, "not empty"):
                run(self.options(output), model_config=self.tiny_model())
            args = parser().parse_args(["--resume", str(output / "last.pt"), "--batch-size", "99", "--epochs", "1"])
            with self.assertRaisesRegex(ValueError, "preserve batch_size"):
                run(args)
        data = json.loads((self.snapshot.path / "manifest.json").read_text()); data["note"] = "changed"
        (self.snapshot.path / "manifest.json").write_text(json.dumps(data))
        args = parser().parse_args(["--resume", str(output / "last.pt"), "--epochs", "1"])
        with self.assertRaisesRegex(ValueError, "snapshot/hash/schema"):
            run(args)

    def test_adaptive_long_span_progress_and_unicode(self):
        class InsideModel:
            config = ModelConfig()
            token_head = type("Head", (), {"out_features": 16})()
            modifier_head = type("Head", (), {"out_features": 3})()
            def eval(self): return self
            def __call__(self, ids, mask):
                length = ids.shape[1]
                out = ModelOutput(torch.full((1, length, 3), -10.), torch.full((1, length, 16), -10.), torch.full((1, length, 3), -10.))
                out.boundary[:, :, 2] = 10
                if ids[0, 0] == ord("a"):
                    out.boundary[0, 0, 1] = 20
                out.token_type[:, :, SCHEMA.token_types.index("variable")] = 10
                return out
        source = "a" + "x\U0001f680" * 400
        out = document_logits(InsideModel(), source, CPU)
        self.assertEqual(decode(source, out, SCHEMA_DICT)["spans"],
                         [{"start": 0, "end": 1201, "tokenType": "variable"}])


if __name__ == "__main__":
    unittest.main()
