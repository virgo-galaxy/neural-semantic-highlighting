"""Release metadata privacy must not alter model tensors or computation."""
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from training.portable import portable_data, portable_text, strip_onnx_debug, computation_bytes
from training.sanitize_release import sanitize_native, sanitize_onnx


class PortableMetadataTests(unittest.TestCase):
    def test_audit_detects_bare_home_and_nested_home_paths(self):
        from training.sanitize_release import has_local_paths
        self.assertTrue(has_local_paths(str(Path.home()).encode()))
        self.assertTrue(has_local_paths(str(Path.home() / "Datasets/project").encode()))
        self.assertFalse(has_local_paths(b"~/Datasets/project"))

    def test_repository_and_home_references_are_portable_and_idempotent(self):
        home = Path("/example/account")
        repository = home / "work/project"
        text = str(repository / "artifacts/run/last.pt")
        self.assertEqual(portable_text(text, repository=repository, home=home), "artifacts/run/last.pt")
        value = portable_text(str(home / "Datasets/project/python"), repository=repository, home=home)
        self.assertEqual(value, "~/Datasets/project/python")
        self.assertEqual(portable_text(value, repository=repository, home=home), value)
        self.assertEqual(portable_text(str(home), repository=repository, home=home), "~")
        self.assertEqual(portable_text(str(home) + "-other/file", repository=repository, home=home),
                         str(home) + "-other/file")

    def test_native_cleanup_preserves_tensor_bytes_and_state_dict_metadata(self):
        state = OrderedDict(weight=torch.tensor([1.25, -0.0, 3.0]))
        state._metadata = {"": {"version": 1}}
        payload = {"model": state, "dataset": {"path": str(Path.home() / "Datasets/project")}}
        self.assertIs(portable_data(payload)["model"]["weight"], state["weight"])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.pt"
            torch.save(payload, path)
            sanitize_native(path)
            actual = torch.load(path, weights_only=True)
            self.assertTrue(torch.equal(actual["model"]["weight"], state["weight"]))
            self.assertEqual(actual["model"]._metadata, state._metadata)
            self.assertEqual(actual["dataset"]["path"], "~/Datasets/project")

    def test_nested_onnx_annotations_are_removed_with_exact_predictions(self):
        try:
            import onnx
            from onnx import helper, TensorProto
        except ImportError:
            self.skipTest("Run with the existing browser-export tool directory on PYTHONPATH")
        node = helper.make_node("Identity", ["input_ids"], ["output"])
        prop = node.metadata_props.add()
        prop.key = "pkg.torch.onnx.stack_trace"
        prop.value = str(Path.home() / "work/model.py")
        node.doc_string = prop.value
        graph = helper.make_graph([node], "identity", [helper.make_tensor_value_info("input_ids", TensorProto.INT64, [1, "bytes"])], [helper.make_tensor_value_info("output", TensorProto.INT64, [1, "bytes"])])
        model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
        model.ir_version = 10
        prop = model.metadata_props.add()
        prop.key, prop.value = "model_license", "MIT"
        fingerprint = computation_bytes(model)
        strip_onnx_debug(model)
        self.assertEqual(computation_bytes(model), fingerprint)
        self.assertEqual(model.metadata_props[0].value, "MIT")
        self.assertEqual(len(model.graph.node[0].metadata_props), 0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "model.onnx"
            onnx.save(model, path)
            self.assertEqual(len(sanitize_onnx(path)["exactOutputLengths"]), 8)

    def test_release_cleanup_preserves_backups_and_refreshes_integrity_links(self):
        from training.sanitize_release import apply, has_local_paths
        with tempfile.TemporaryDirectory() as folder:
            root = (Path(folder) / "project").resolve()
            native = root / "packs/demo/model/model.pt"
            native.parent.mkdir(parents=True)
            torch.save({"model": {"weight": torch.tensor([1.25])},
                        "dataset": {"path": str(Path.home() / "Datasets/project/demo")}}, native)
            report = native.parent / "reports/test.json"
            report.parent.mkdir()
            report.write_text(json.dumps({"f1": 0.95, "source": str(Path.home() / "reports/input.json")}))
            sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            metadata = native.with_suffix(".json")
            metadata.write_text(json.dumps({"artifact": {"file": "model.pt", "sha256": sha(native)},
                "reports": {"test": {"file": "reports/test.json", "sha256": sha(report)}}}))
            files = [native, report, metadata]
            originals = {path.relative_to(root): path.read_bytes() for path in files}
            backup = Path(folder) / "originals"
            with patch("training.sanitize_release.REPOSITORY", root):
                result = apply(backup, files)
            self.assertEqual(result["nativeArtifacts"], 1)
            for path in files:
                self.assertFalse(has_local_paths(path.read_bytes()))
                self.assertEqual((backup / path.relative_to(root)).read_bytes(), originals[path.relative_to(root)])
            actual = json.loads(metadata.read_text())
            self.assertEqual(actual["artifact"]["sha256"], sha(native))
            self.assertEqual(actual["reports"]["test"]["sha256"], sha(report))
            self.assertEqual(json.loads(report.read_text())["f1"], 0.95)


if __name__ == "__main__":
    unittest.main()
