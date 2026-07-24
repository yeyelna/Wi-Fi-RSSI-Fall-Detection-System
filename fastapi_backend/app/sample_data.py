from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import zipfile

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TESTING_ZIP_FILE = DATA_DIR / "testing_data.zip"


def _is_safe_mat_relative(relative_path: str) -> str:
    rel = str(relative_path).replace("\\", "/").strip().lstrip("/")
    if not rel or rel.endswith("/"):
        raise ValueError("Invalid saved testing data path.")

    parts = Path(rel).parts
    if any(part in {"..", ""} for part in parts):
        raise ValueError("Invalid saved testing data path.")

    if Path(rel).suffix.lower() != ".mat":
        raise ValueError("Saved testing data must be a .mat file.")

    return rel


def _normalise_zip_display_name(name: str) -> Dict:
    display_rel = str(name).replace("\\", "/").strip().lstrip("/")

    if display_rel.startswith("testing_data/"):
        display_rel = display_rel[len("testing_data/"):]

    file_name = Path(display_rel).name
    event = Path(display_rel).parent.as_posix() if Path(display_rel).parent != Path(".") else ""

    return {
        "file_name": file_name,
        "event": event,
        "display_label": f"{event} / {file_name}" if event else file_name,
    }


def list_sample_testing_files() -> List[Dict]:
    if not TESTING_ZIP_FILE.exists():
        return []

    items: List[Dict] = []

    try:
        with zipfile.ZipFile(TESTING_ZIP_FILE) as zf:
            for info in sorted(zf.infolist(), key=lambda x: x.filename):
                name = info.filename.replace("\\", "/")

                if info.is_dir() or not name.lower().endswith(".mat"):
                    continue

                display = _normalise_zip_display_name(name)

                items.append({
                    **display,
                    "relative_path": name,
                    "size_bytes": int(info.file_size),
                    "source": "testing_data.zip",
                })

    except zipfile.BadZipFile:
        return []

    return items


def read_sample_testing_file(relative_path: str) -> Tuple[str, bytes]:
    rel = _is_safe_mat_relative(relative_path)

    if not TESTING_ZIP_FILE.exists():
        raise FileNotFoundError("Saved testing data zip file not found.")

    with zipfile.ZipFile(TESTING_ZIP_FILE) as zf:
        candidates = [rel]

        if not rel.startswith("testing_data/"):
            candidates.append("testing_data/" + rel)

        for candidate in candidates:
            try:
                with zf.open(candidate) as f:
                    return Path(candidate).name, f.read()
            except KeyError:
                continue

    raise FileNotFoundError("Saved testing data file not found inside testing_data.zip.")
