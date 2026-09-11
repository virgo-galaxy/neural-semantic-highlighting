"""Bounded, syntax-proven legacy Gold repair using the project's Go parser."""
from __future__ import annotations

from bisect import bisect_left
from contextlib import AbstractContextManager
import json
import os
from pathlib import Path
import subprocess
from typing import Any


class SyntaxRepairer(AbstractContextManager):
    """One lazy JSONL process per preparation; never relabel or rewrite a corpus.

    Only documents with gaps and a possible switch are sent to the parser. The
    parser reports explicit type-switch declarations, not guesses about names.
    The exact Go toolchain is scoped to this child process, not written globally.
    """

    def __init__(self, repository: Path, toolchain: str):
        self.repository = repository
        self.toolchain = toolchain
        self.process: subprocess.Popen | None = None

    def _command(self) -> list[str]:
        return ["go", "run", "./labeling/cmd/nsh-go-syntax-repair"]

    def _start(self) -> None:
        if self.process is not None:
            return
        environment = dict(os.environ, GOTOOLCHAIN=self.toolchain, GOWORK="off")
        self.process = subprocess.Popen(
            self._command(), cwd=self.repository / "packs/go", env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            # Stderr remains visible; a child crash must not deadlock on a pipe.
            text=True, encoding="utf-8", bufsize=1,
        )

    def declarations(self, source: str) -> list[dict[str, Any]]:
        self._start()
        assert self.process is not None and self.process.stdin is not None and self.process.stdout is not None
        try:
            self.process.stdin.write(json.dumps({"source": source}, ensure_ascii=True) + "\n")
            self.process.stdin.flush()
            line = self.process.stdout.readline()
        except (BrokenPipeError, OSError) as error:
            raise ValueError("Go syntax repair process failed; inspect its stderr") from error
        if not line:
            raise ValueError("Go syntax repair process stopped; inspect its stderr and toolchain")
        result = json.loads(line)
        if not isinstance(result.get("spans"), list):
            raise ValueError("Invalid response from Go syntax repair process")
        return result["spans"]

    def repair(self, record: dict) -> tuple[dict, int]:
        # This is only a cheap negative filter. Positive matches are always
        # parsed by go/parser; regex is never used to identify declarations.
        if "switch" not in record["source"]:
            return record, 0
        return apply_type_switch_declarations(record, self.declarations(record["source"]))

    def __exit__(self, exc_type, exc_value, traceback):
        if self.process is not None:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                try:
                    code = self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                    code = -1
                if code != 0 and exc_type is None:
                    raise ValueError(f"Go syntax repair process exited with status {code}")
            finally:
                if self.process.stdout:
                    self.process.stdout.close()
        return False


def apply_type_switch_declarations(record: dict, candidates: list[dict]) -> tuple[dict, int]:
    """Fill completely uncovered parser-confirmed identifiers; never override Gold."""
    result = record["result"]
    if result.get("offsetEncoding") != "utf-16":
        raise ValueError("Syntax repair requires UTF-16 Gold offsets")
    original = result["spans"]
    starts = [span["start"] for span in original]
    source_length = len(record["source"].encode("utf-16-le")) // 2
    repairs = []
    seen = set()
    for candidate in candidates:
        lo, hi = candidate.get("start"), candidate.get("end")
        if (type(lo) is not int or type(hi) is not int or not 0 <= lo < hi <= source_length
                or candidate.get("tokenType") != "variable"
                or candidate.get("modifiers") != ["declaration"]):
            raise ValueError("Invalid parser-confirmed type-switch declaration")
        if (lo, hi) in seen:
            continue
        seen.add((lo, hi))
        index = bisect_left(starts, lo)
        overlaps = []
        if index > 0 and original[index-1]["end"] > lo:
            overlaps.append(original[index-1])
        if index < len(original) and original[index]["start"] < hi:
            overlaps.append(original[index])
        if overlaps:
            if len(overlaps) == 1 and overlaps[0] == candidate:
                continue
            raise ValueError("Parser-confirmed declaration conflicts with existing Gold; not overwritten")
        repairs.append(candidate)
    if not repairs:
        return record, 0
    combined = sorted(original + repairs, key=lambda span: span["start"])
    if any(left["end"] > right["start"] for left, right in zip(combined, combined[1:])):
        raise ValueError("Overlapping syntax repair candidates")
    updated = {**record, "result": {**result, "spans": combined},
               "goldRepairs": {**record.get("goldRepairs", {}),
                               "legacyTypeSwitchDeclarations": len(repairs)}}
    return updated, len(repairs)
