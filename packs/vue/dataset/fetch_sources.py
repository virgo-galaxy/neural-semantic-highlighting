"""Fetch only pinned Vue Vue/license blobs; verify Git identity and freeze SHA-256 locks."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import quote, urlsplit


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def download(url: str, limit: int) -> bytes:
    if urlsplit(url).scheme != "https" or urlsplit(url).hostname not in {"api.github.com", "raw.githubusercontent.com"}:
        raise ValueError("Only official pinned GitHub source endpoints are allowed")
    raw = subprocess.check_output(["curl", "--fail", "--location", "--proto", "=https", "--proto-redir", "=https",
        "--silent", "--show-error", "--max-time", "45", "--max-filesize", str(limit), url])
    if len(raw) > limit:
        raise ValueError("Source response exceeds the explicit limit")
    return raw


def fetch(root: Path, config: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".fetch.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()) + "\n")
        for spec in json.loads(config.read_text())["sources"]:
            repo, commit, name = spec["repository"], spec["commit"], spec["id"]
            if (not re.fullmatch(r"vuejs/(vuex|pinia)", repo) or not re.fullmatch(r"[a-f0-9]{40}", commit)
                    or not re.fullmatch(r"[a-z0-9-]+", name) or not spec["prefixes"]
                    or any(PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts for p in spec["prefixes"])):
                raise ValueError("Invalid explicitly pinned Vue source")
            target = root / (name + "-" + commit[:12])
            if target.exists():
                saved = json.loads((target / "source.lock.json").read_text())
                if saved["sourceSpec"] != spec:
                    raise ValueError("Existing immutable source selection differs")
                for path, expected in saved["files"].items():
                    item = target / path
                    if not item.resolve().is_relative_to(target.resolve()) or digest(item.read_bytes()) != expected:
                        raise ValueError("Locked source was modified: " + path)
                print(f"Reused {repo}@{commit[:12]}: {len(saved['files'])} files", flush=True)
                continue
            tree = json.loads(download(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1", 8 << 20))
            if tree.get("truncated"):
                raise ValueError("Truncated source tree cannot establish complete coverage")
            entries = []
            for item in tree["tree"]:
                path = PurePosixPath(item["path"])
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Unsafe Git source path")
                if item["type"] != "blob" or item.get("mode") not in {"100644", "100755"}:
                    continue
                license_file = len(path.parts) == 1 and path.name.lower().startswith(("license", "licence", "copying"))
                vue_file = str(path).lower().endswith((".vue",)) and any(str(path).startswith(p) for p in spec["prefixes"])
                if license_file or vue_file:
                    if item.get("size", 0) > 500_000:
                        raise ValueError("Selected Vue blob exceeds the source limit")
                    entries.append(item)
            if not any(item["path"].lower().endswith((".vue",)) for item in entries) or len(entries) > 500:
                raise ValueError("Pinned selection has no Vue or exceeds the explicit budget")
            staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
            try:
                def retrieve(item):
                    raw = download(f"https://raw.githubusercontent.com/{repo}/{commit}/{quote(item['path'], safe='/')}", 500_000)
                    git_hash = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest()
                    if git_hash != item["sha"]:
                        raise ValueError("Git blob identity mismatch: " + item["path"])
                    destination = staging / item["path"]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(raw)
                    return item["path"], digest(raw)
                with ThreadPoolExecutor(max_workers=4) as pool:
                    files = dict(pool.map(retrieve, entries))
                identity = {"sourceSpec": spec, "spec": {"name": repo, "version": commit},
                    "upstream": "https://github.com/" + repo, "commit": commit, "tree": tree["sha"],
                    "integrity": "git-tree:" + tree["sha"], "files": dict(sorted(files.items())),
                    "gitBlobs": {item["path"]: item["sha"] for item in entries}}
                (staging / "source.lock.json").write_text(json.dumps(identity, indent=2) + "\n")
                staging.rename(target)
                print(f"Fetched {repo}@{commit[:12]}: {len(files)} Vue/license files", flush=True)
            finally:
                if staging.exists(): shutil.rmtree(staging)
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(os.environ.get(
        "NSH_DATASET_ROOT", "~/Datasets/neural-semantic-highlighting")).expanduser() / "vue/sources")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("git-sources.json"))
    args = parser.parse_args()
    fetch(args.root.expanduser().resolve(), args.config)


if __name__ == "__main__": main()
