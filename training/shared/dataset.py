"""Memory-mapped access to prepared pack windows without loading a whole corpus."""
from __future__ import annotations

from training.shared.spec import current

from array import array
import json
import mmap
from pathlib import Path
import struct
import sys

from training.shared.encoding import COLUMNS, IGNORE, PAD


class WindowDataset:
    """Standard-library reader. A trainer can convert each returned row to tensors.

    Attention masks hide padding, while label masks also hide UTF-8 continuation
    bytes. Modifier bits are interpreted in the exact schema order in manifest.json.
    """

    def __init__(self, snapshot: Path, split: str) -> None:
        if split not in {"train", "validation", "test"}:
            raise ValueError("Unknown dataset split")
        self.manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
        if self.manifest.get("format") != current().dataset_format:
            raise ValueError("Unsupported prepared pack dataset format")
        self.size = self.manifest["contextBytes"]
        self.count = self.manifest["splits"][split]["windows"]
        self._files = {}
        self._maps = {}
        try:
            for name, typecode in COLUMNS.items():
                path = snapshot / split / (name + ".bin")
                expected = self.size * self.count * array(typecode).itemsize
                if path.stat().st_size != expected:
                    raise ValueError(f"Truncated or incompatible column: {path}")
                stream = path.open("rb")
                self._files[name] = stream
                self._maps[name] = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) if expected else None
        except Exception:
            self.close()
            raise

    def __len__(self) -> int:
        return self.count

    def __getitem__(self, index: int) -> dict:
        if index < 0:
            index += self.count
        if not 0 <= index < self.count:
            raise IndexError(index)
        row = {}
        for name, code in COLUMNS.items():
            itemsize = struct.calcsize("<" + code)
            offset = index * self.size * itemsize
            values = array(code)
            values.frombytes(self._maps[name][offset:offset + self.size * itemsize])
            if sys.byteorder != "little" and itemsize > 1:
                values.byteswap()
            row[name] = values
        row["attention_mask"] = [value != PAD for value in row["input_ids"]]
        row["label_mask"] = [value != IGNORE for value in row["boundary_labels"]]
        # Only BEGIN positions receive modifier supervision, including negative
        # examples for spans without a modifier. Do not treat INSIDE as negatives.
        row["modifier_mask"] = [value == 1 for value in row["boundary_labels"]]
        return row

    def close(self) -> None:
        for memory in getattr(self, "_maps", {}).values():
            if memory is not None:
                memory.close()
        for stream in getattr(self, "_files", {}).values():
            stream.close()
        self._maps = {}
        self._files = {}

    def __enter__(self) -> WindowDataset:
        return self

    def __exit__(self, *_args) -> None:
        self.close()
