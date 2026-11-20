"""Remove local paths from current repository artifacts, never Git history or datasets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from training.portable import REPOSITORY, computation_bytes, portable_data, portable_text, strip_onnx_debug


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_files() -> list[Path]:
    raw = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=REPOSITORY,
    )
    return sorted({REPOSITORY / name.decode() for name in raw.split(b"\0") if name
                   and (REPOSITORY / name.decode()).is_file()})


def has_local_paths(raw: bytes) -> bool:
    import re
    # Concrete home paths in release provenance; generic source-code examples
    # such as /Users/virgo/Documents are not current-machine identities.
    return str(Path.home()).encode() in raw or bool(re.search(
        rb"/(?:private/)?var/folders/[^/\s\x00\"]+/[^/\s\x00\"]+/[A-Za-z0-9_]+", raw,
    ))


def verify_payload(expected, actual) -> None:
    import torch
    if torch.is_tensor(expected):
        if (expected.dtype != actual.dtype or expected.shape != actual.shape
                or not torch.equal(expected.detach().cpu().contiguous().reshape(-1).view(torch.uint8),
                                   actual.detach().cpu().contiguous().reshape(-1).view(torch.uint8))):
            raise ValueError("Model tensor bytes changed")
    elif isinstance(expected, dict):
        if list(expected) != list(actual):
            raise ValueError("Model metadata keys changed unexpectedly")
        for key in expected:
            verify_payload(expected[key], actual[key])
        if hasattr(expected, "_metadata"):
            verify_payload(expected._metadata, actual._metadata)
    elif isinstance(expected, (list, tuple)):
        if type(expected) is not type(actual) or len(expected) != len(actual):
            raise ValueError("Model metadata sequence changed")
        for a, b in zip(expected, actual):
            verify_payload(a, b)
    elif expected != actual:
        raise ValueError("Non-path model metadata changed")


def sanitize_native(path: Path) -> dict:
    import torch
    original = torch.load(path, map_location="cpu", weights_only=True)
    clean = portable_data(original)
    temporary = path.with_suffix(".sanitized.tmp")
    try:
        with temporary.open("wb") as stream:
            torch.save(clean, stream)
        reloaded = torch.load(temporary, map_location="cpu", weights_only=True)
        verify_payload(clean, reloaded)
        if has_local_paths(temporary.read_bytes()):
            raise ValueError("Native artifact still contains a local path")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return {"tensorBytesUnchanged": True, "portableMetadataReloaded": True}


def sanitize_onnx(path: Path) -> dict:
    import numpy as np
    import onnx
    import onnxruntime as ort

    original = onnx.load(path)
    signature = computation_bytes(original)
    original_bytes = path.read_bytes()
    strip_onnx_debug(original)
    if computation_bytes(original) != signature:
        raise ValueError("ONNX computation changed")
    onnx.checker.check_model(original)
    encoded = original.SerializeToString(deterministic=True)
    if has_local_paths(encoded):
        raise ValueError("ONNX artifact still contains a local path")

    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    before = ort.InferenceSession(original_bytes, sess_options=options, providers=["CPUExecutionProvider"])
    after = ort.InferenceSession(encoded, sess_options=options, providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(1729)
    lengths = [1, 2, 7, 31, 64, 127, 511, 512]
    for length in lengths:
        inputs = {"input_ids": rng.integers(0, 256, size=(1, length), dtype=np.int64)}
        for a, b in zip(before.run(None, inputs), after.run(None, inputs)):
            if not np.array_equal(a, b):
                raise ValueError(f"ONNX predictions changed at {length} bytes")
    path.write_bytes(encoded)
    return {"computationSha256": hashlib.sha256(signature).hexdigest(),
            "computationAndTensorBytesUnchanged": True, "exactOutputLengths": lengths}


def apply(backup: Path, files: list[Path]) -> dict:
    backup = backup.resolve()
    if backup == REPOSITORY or REPOSITORY in backup.parents:
        raise ValueError("Keep original local-path backups outside the repository")
    backup.mkdir(parents=True, exist_ok=False)
    originals = {str(path.relative_to(REPOSITORY)): digest(path) for path in files}
    known_hashes = {name: {value} for name, value in originals.items()}
    records = []
    saved = set()

    def preserve(path):
        relative = path.relative_to(REPOSITORY)
        if relative not in saved:
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            saved.add(relative)

    # Current tracked text is rewritten without reformatting reports or source probes.
    for path in files:
        if path.suffix in {".pt", ".onnx"}:
            continue
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        clean = portable_text(text)
        if clean != text:
            preserve(path)
            path.write_bytes(clean.encode("utf-8"))
            known_hashes[str(path.relative_to(REPOSITORY))].add(digest(path))

    for path in files:
        if path.suffix not in {".pt", ".onnx"} or not has_local_paths(path.read_bytes()):
            continue
        preserve(path)
        verification = sanitize_native(path) if path.suffix == ".pt" else sanitize_onnx(path)
        row = {"file": str(path.relative_to(REPOSITORY)),
               "beforeSha256": originals[str(path.relative_to(REPOSITORY))],
               "afterSha256": digest(path), **verification}
        records.append(row)
        known_hashes[row["file"]].add(row["afterSha256"])
        print(json.dumps({"sanitized": row["file"], "verified": True}), flush=True)

    # Refresh file-integrity links, not historical training-checkpoint provenance.
    changed_hashes = {row["beforeSha256"]: row["afterSha256"] for row in records}
    native_by_original = {}
    for row in records:
        if row["file"].endswith(".pt"):
            native_by_original.setdefault(row["beforeSha256"], []).append(row["file"])

    def file_reference(filename: str, owner: Path):
        raw = Path(filename).expanduser()
        candidates = [owner.parent / raw, REPOSITORY / raw] if not raw.is_absolute() else [raw]
        return next((candidate for candidate in candidates
                     if candidate.is_file() and candidate.resolve().is_relative_to(REPOSITORY)
                     and str(candidate.resolve().relative_to(REPOSITORY)) in originals), None)

    def refresh(value, owner):
        if isinstance(value, dict):
            for key, item in list(value.items()):
                if (key in {"modelSha256", "browserSha256", "sourceSha256"}
                        and isinstance(item, str) and item in changed_hashes):
                    value[key] = changed_hashes[item]
                else:
                    refresh(item, owner)
            if isinstance(value.get("file"), str) and isinstance(value.get("sha256"), str):
                target = file_reference(value["file"], owner)
                if target:
                    relative = str(target.resolve().relative_to(REPOSITORY))
                    # Only identities that really identified this tracked file are refreshed.
                    if value["sha256"] in known_hashes[relative]:
                        value["sha256"] = digest(target)
                        if "bytes" in value:
                            value["bytes"] = target.stat().st_size
        elif isinstance(value, list):
            for item in value:
                refresh(item, owner)

    # Model sidecars point at their actual sibling artifact, including archived bundles.
    for path in files:
        if path.name != "model.json" or path.suffix != ".json":
            continue
        value = json.loads(path.read_text())
        if value.get("format") == "nsh-browser-model-v1":
            old_source = value["source"]["sha256"]
            alternatives = native_by_original.get(old_source, [])
            current = REPOSITORY / value["source"]["file"]
            if alternatives and (not current.exists()
                                 or originals.get(value["source"]["file"]) != old_source):
                sibling = str(path.parent.relative_to(REPOSITORY)).replace("/browser", "/model") + "/model.pt"
                value["source"]["file"] = sibling if sibling in alternatives else alternatives[0]
            source_file = value["source"]["file"]
            if alternatives or originals.get(source_file) == old_source:
                value["source"]["sha256"] = digest(REPOSITORY / source_file)
        refresh(value, path)
        clean = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        # Avoid rewriting sidecars whose data has not changed.
        if json.loads(path.read_text()) != value:
            preserve(path)
            path.write_text(clean)
            known_hashes[str(path.relative_to(REPOSITORY))].add(digest(path))

    # Reports can be referenced by sidecars, so repeat bounded propagation until stable.
    for _ in range(8):
        altered = False
        for path in files:
            if path.suffix != ".json":
                continue
            try:
                original = json.loads(path.read_text())
            except ValueError:
                continue
            import copy
            value = copy.deepcopy(original)
            refresh(value, path)
            if value != original:
                preserve(path)
                path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
                known_hashes[str(path.relative_to(REPOSITORY))].add(digest(path))
                altered = True
        if not altered:
            break
    else:
        raise ValueError("File-integrity references did not converge")

    remaining = [str(path.relative_to(REPOSITORY)) for path in files if has_local_paths(path.read_bytes())]
    if remaining:
        raise ValueError("Local paths remain in: " + ", ".join(remaining))
    report = {"format": "nsh-portable-release-v1", "gitHistoryChanged": False,
              "externalDatasetsChanged": False, "retrained": False,
              "nativeArtifacts": sum(row["file"].endswith(".pt") for row in records),
              "browserArtifacts": sum(row["file"].endswith(".onnx") for row in records),
              "changedCurrentFiles": len(saved), "artifacts": records}
    (backup / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    files = current_files()
    if args.apply:
        if args.backup_dir is None:
            parser.error("--apply requires an external --backup-dir")
        report = apply(args.backup_dir, files)
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({key: value for key, value in report.items() if key != "artifacts"}, indent=2))
    else:
        matches = [str(path.relative_to(REPOSITORY)) for path in files if has_local_paths(path.read_bytes())]
        print(json.dumps({"scope": "current repository files; ignored environment/cache files excluded",
                          "matches": matches}, indent=2))
        raise SystemExit(bool(matches))


if __name__ == "__main__":
    main()
