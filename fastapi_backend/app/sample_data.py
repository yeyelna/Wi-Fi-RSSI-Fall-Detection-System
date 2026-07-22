from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample_testing_data"


def _safe_sample_path(relative_path: str) -> Path:
    base = SAMPLE_DATA_DIR.resolve()
    candidate = (SAMPLE_DATA_DIR / str(relative_path)).resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("Invalid saved testing data path.")
    if candidate.suffix.lower() != ".mat":
        raise ValueError("Saved testing data must be a .mat file.")
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError("Saved testing data file not found.")
    return candidate


def list_sample_testing_files() -> List[Dict]:
    if not SAMPLE_DATA_DIR.exists():
        return []

    items: List[Dict] = []
    for path in sorted(SAMPLE_DATA_DIR.rglob("*.mat")):
        rel = path.relative_to(SAMPLE_DATA_DIR)
        event = rel.parent.as_posix() if rel.parent != Path(".") else ""
        items.append({
            "file_name": path.name,
            "event": event,
            "relative_path": rel.as_posix(),
            "display_label": f"{event} / {path.name}" if event else path.name,
            "size_bytes": path.stat().st_size,
        })
    return items


def read_sample_testing_file(relative_path: str) -> Tuple[str, bytes]:
    path = _safe_sample_path(relative_path)
    return path.name, path.read_bytes()
