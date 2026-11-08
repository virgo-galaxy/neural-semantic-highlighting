"""Bind the shared neural implementation as well as Vue-specific experiment code."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]

def code_hashes():
    files = list(Path(__file__).parent.glob("*.py"))
    files += [ROOT / "training/html" / name for name in ("model.py", "inference.py", "losses.py", "io.py")]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
