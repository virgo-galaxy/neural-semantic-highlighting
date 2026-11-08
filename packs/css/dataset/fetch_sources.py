"""Fetch only explicitly pinned style sources; verify registry integrity and execute nothing."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile
from urllib.parse import urlsplit


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def download(url: str, limit: int) -> bytes:
    if urlsplit(url).scheme != "https" or urlsplit(url).hostname != "registry.npmjs.org":
        raise ValueError("Style source downloads must use the npm registry")
    # Use curl's platform trust store on macOS. Keep normal TLS verification;
    # never use an unverified Python SSL context or curl --insecure.
    data = subprocess.check_output(["curl", "--fail", "--location", "--proto", "=https",
        "--proto-redir", "=https", "--max-time", "60", "--max-filesize", str(limit),
        "--silent", "--show-error", url])
    if len(data) > limit:
        raise ValueError("Source download exceeds the explicit size limit")
    return data


def fetch(root: Path, config: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".fetch.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()) + "\n")
        for spec in json.loads(config.read_text())["packages"]:
            name, version, directory = spec["name"], spec["version"], spec["directory"]
            if (not re.fullmatch(r"[a-z0-9-]+", name) or not re.fullmatch(r"\d+\.\d+\.\d+", version)
                    or directory != name + "-" + version or spec["suffix"] not in {".css", ".scss", ".less"}
                    or ".." in PurePosixPath(spec["prefix"]).parts):
                raise ValueError("Invalid pinned style source")
            target = root / directory
            if target.exists():
                saved = json.loads((target / "source.lock.json").read_text())
                if saved["spec"] != spec:
                    raise ValueError("Existing source lock differs from the pinned configuration")
                for path, expected in saved["files"].items():
                    file = target / path
                    if not file.resolve().is_relative_to(target.resolve()) or digest(file.read_bytes()) != expected:
                        raise ValueError("Locked source was modified: " + str(file))
                print(f"Reused {name}@{version}: {len(saved['files'])} source/license files", flush=True)
                continue
            metadata = json.loads(download(f"https://registry.npmjs.org/{name}/{version}", 4 << 20))
            if metadata["name"] != name or metadata["version"] != version:
                raise ValueError("Registry package identity mismatch")
            distribution = metadata["dist"]
            raw = download(distribution["tarball"], 32 << 20)
            actual = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode("ascii")
            if actual not in distribution["integrity"].split():
                raise ValueError("Registry tarball integrity mismatch")
            staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
            try:
                files, total = {}, 0
                with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
                    for member in archive:
                        path = PurePosixPath(member.name)
                        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "package":
                            raise ValueError("Unsafe source archive path")
                        if not member.isfile():
                            continue
                        relative = PurePosixPath(*path.parts[1:])
                        text = str(relative)
                        selected = text.startswith(spec["prefix"]) and text.endswith(spec["suffix"])
                        license_file = len(relative.parts) == 1 and relative.name.lower().startswith(("license", "licence"))
                        if not selected and not license_file:
                            continue
                        total += member.size
                        if total > 50 << 20:
                            raise ValueError("Selected source files exceed the size limit")
                        stream = archive.extractfile(member)
                        if stream is None:
                            raise ValueError("Missing archive file contents")
                        content = stream.read()
                        destination = staging / text
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(content)
                        files[text] = digest(content)
                if not any(path.endswith(spec["suffix"]) for path in files):
                    raise ValueError("Pinned archive contains no selected style source")
                identity = {"spec": spec, "tarball": distribution["tarball"],
                    "integrity": distribution["integrity"], "archiveSha256": digest(raw),
                    "license": metadata.get("license"), "files": dict(sorted(files.items()))}
                (staging / "source.lock.json").write_text(json.dumps(identity, indent=2) + "\n")
                staging.rename(target)
                print(f"Fetched {name}@{version}: {len(files)} source/license files, {total} bytes", flush=True)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
    finally:
        lock.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(os.environ.get(
        "NSH_DATASET_ROOT", "~/Datasets/neural-semantic-highlighting")).expanduser() / "css/sources")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("packages.json"))
    args = parser.parse_args()
    fetch(args.root.expanduser().resolve(), args.config)


if __name__ == "__main__":
    main()
