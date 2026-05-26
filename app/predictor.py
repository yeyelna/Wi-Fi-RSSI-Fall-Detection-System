import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model_artifacts"
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")
TIMESTAMP_TIMEZONE = "Asia/Kuala_Lumpur"
TIMESTAMP_OFFSET = "+08:00"
USER_FRIENDLY_NOT_FOUND = "File not supported for fast classification. Please choose a test file from the prepared dataset."

def _normalize_lookup_text(value) -> str:
    """Normalize Windows/Linux paths for reliable lookup on Render/Linux."""
    return str(value).strip().replace("\\", "/").lower()


def _basename_any_path(value) -> str:
    """Return filename even when the stored path uses Windows backslashes."""
    return Path(str(value).strip().replace("\\", "/")).name


MTFF_BLOCKS = {
    "FFT": np.arange(0, 128),
    "STFT": np.arange(128, 256),
    "CWT": np.arange(256, 384),
}


def _safe_skew_kurtosis(block):
    eps = 1e-12
    mean = np.mean(block, axis=1, keepdims=True)
    std = np.std(block, axis=1, keepdims=True) + eps
    z = (block - mean) / std
    return np.mean(z ** 3, axis=1), np.mean(z ** 4, axis=1)


def _safe_entropy_abs(block):
    eps = 1e-12
    a = np.abs(block)
    p = a / (np.sum(a, axis=1, keepdims=True) + eps)
    return -np.sum(p * np.log(p + eps), axis=1) / np.log(block.shape[1])


def build_mtff_plus_features(X384):
    X384 = np.asarray(X384, dtype=np.float32)
    derived_arrays = []
    block_summary = {}

    for block_name, idx in MTFF_BLOCKS.items():
        block = X384[:, idx]
        abs_block = np.abs(block)
        q25 = np.percentile(block, 25, axis=1)
        q75 = np.percentile(block, 75, axis=1)
        skew, kurt = _safe_skew_kurtosis(block)
        entropy_abs = _safe_entropy_abs(block)

        quarters = np.array_split(np.arange(block.shape[1]), 4)
        q_energy = []
        for q_idx in quarters:
            qe = np.sum(block[:, q_idx] ** 2, axis=1)
            q_energy.append(qe)
            derived_arrays.append(qe.reshape(-1, 1))

        features = {
            "mean": np.mean(block, axis=1),
            "std": np.std(block, axis=1),
            "min": np.min(block, axis=1),
            "max": np.max(block, axis=1),
            "median": np.median(block, axis=1),
            "q25": q25,
            "q75": q75,
            "iqr": q75 - q25,
            "range": np.max(block, axis=1) - np.min(block, axis=1),
            "energy": np.sum(block ** 2, axis=1),
            "abs_energy": np.sum(abs_block ** 2, axis=1),
            "l1": np.sum(abs_block, axis=1),
            "l2": np.sqrt(np.sum(block ** 2, axis=1)),
            "max_abs": np.max(abs_block, axis=1),
            "abs_mean": np.mean(abs_block, axis=1),
            "abs_std": np.std(abs_block, axis=1),
            "argmax_norm": np.argmax(abs_block, axis=1) / max(1, block.shape[1] - 1),
            "positive_ratio": np.mean(block > 0, axis=1),
            "skew": skew,
            "kurtosis": kurt,
            "entropy_abs": entropy_abs,
            "early_late_energy_ratio": q_energy[0] / (q_energy[-1] + 1e-12),
            "mid_edge_energy_ratio": (q_energy[1] + q_energy[2]) / (q_energy[0] + q_energy[3] + 1e-12),
        }
        block_summary[block_name] = features
        for values in features.values():
            derived_arrays.append(values.reshape(-1, 1))

    for a, b in [("FFT", "STFT"), ("FFT", "CWT"), ("STFT", "CWT")]:
        for stat in ["energy", "abs_energy", "std", "abs_mean", "entropy_abs", "max_abs"]:
            va = block_summary[a][stat]
            vb = block_summary[b][stat]
            derived_arrays.append((va / (vb + 1e-12)).reshape(-1, 1))
            derived_arrays.append((va - vb).reshape(-1, 1))

    total_energy = (
        block_summary["FFT"]["energy"]
        + block_summary["STFT"]["energy"]
        + block_summary["CWT"]["energy"]
        + 1e-12
    )
    for block_name in ["FFT", "STFT", "CWT"]:
        share = block_summary[block_name]["energy"] / total_energy
        derived_arrays.append(share.reshape(-1, 1))

    return np.hstack([X384] + derived_arrays).astype(np.float32)


def safe_binary_probability(model, X):
    if model is None:
        return np.ones(X.shape[0], dtype=float)
    return model.predict_proba(X)[:, 1]


def event_fall_probability(event_model, X, event_classes, fall_class_ids):
    probs = event_model.predict_proba(X)
    if probs.ndim == 1:
        probs = probs.reshape(-1, 1)
    if hasattr(event_model, "classes_"):
        aligned = np.zeros((X.shape[0], len(event_classes)), dtype=float)
        for col_pos, class_id in enumerate(event_model.classes_):
            aligned[:, int(class_id)] = probs[:, col_pos]
        probs = aligned
    return np.sum(probs[:, list(fall_class_ids)], axis=1)


def combine_probabilities(primary_prob, gate_prob, event_fall_prob, alpha, beta):
    primary_prob = np.asarray(primary_prob, dtype=float)
    gate_prob = np.asarray(gate_prob, dtype=float)
    event_fall_prob = np.asarray(event_fall_prob, dtype=float)
    p_gate = primary_prob * (1.0 - float(alpha) * (1.0 - gate_prob))
    p_event = (1.0 - float(beta)) * p_gate + float(beta) * event_fall_prob
    return np.clip(p_event, 0.0, 1.0)


class MTFFPredictor:
    def __init__(self):
        package_path = MODEL_DIR / "mtff_event_aware_veto_inference_package.pkl"
        if not package_path.exists():
            raise FileNotFoundError(f"Missing model package: {package_path}")
        data_path = DATA_DIR / "MTFF_384.csv"
        if not data_path.exists():
            raise FileNotFoundError(f"Missing feature bank: {data_path}")

        self.package = joblib.load(package_path)
        self.primary_model = self.package["primary_model"]
        self.gate_model = self.package.get("gate_model")
        self.event_model = self.package["event_model"]
        self.scaler = self.package["scaler"]
        self.selected_feature_indices = list(self.package["selected_feature_indices"])
        self.selected_feature_names = list(self.package["selected_feature_names"])
        self.mtff_feature_columns_384 = list(self.package["mtff_feature_columns_384"])
        self.event_classes = list(self.package["event_classes"])
        self.fall_class_ids = set(int(i) for i in self.package["fall_class_ids"])
        self.alpha = float(self.package["alpha"])
        self.beta = float(self.package["beta"])
        self.threshold = float(self.package["threshold"])

        model_info_path = MODEL_DIR / "model_info.json"
        if model_info_path.exists():
            with open(model_info_path, "r", encoding="utf-8") as f:
                self.model_info = json.load(f)
        else:
            self.model_info = {}

        self.feature_bank = pd.read_csv(data_path)
        self.feature_bank["File_lookup_full"] = self.feature_bank["File"].astype(str).apply(_normalize_lookup_text)
        self.feature_bank["File_lookup_name"] = self.feature_bank["File"].astype(str).apply(
            lambda x: _basename_any_path(x).lower()
        )

        available_path = DATA_DIR / "available_files.json"
        if available_path.exists():
            with open(available_path, "r", encoding="utf-8") as f:
                self.available_files = json.load(f)
        else:
            self.available_files = [{"file_name": str(x)} for x in self.feature_bank["File"].astype(str).tolist()]

        # Add display fields for dashboard dropdowns without changing the original file_name.
        for item in self.available_files:
            raw_name = item.get("file_name") or item.get("filename") or ""
            item["display_name"] = _basename_any_path(raw_name)
            item["lookup_name"] = item["display_name"].lower()

    @property
    def model_loaded(self) -> bool:
        return self.primary_model is not None and self.event_model is not None

    @property
    def feature_bank_loaded(self) -> bool:
        return self.feature_bank is not None and len(self.feature_bank) > 0

    def get_model_info(self) -> Dict:
        info = dict(self.model_info)
        info.update({
            "display_model_name": info.get("display_model_name", "MTFF Event-Aware Veto"),
            "classifier": info.get("classifier", "LightGBM"),
            "threshold": self.threshold,
            "alpha_gate": self.alpha,
            "beta_event": self.beta,
            "selected_feature_count": len(self.selected_feature_indices),
            "timestamp_timezone": TIMESTAMP_TIMEZONE,
            "timestamp_gmt_offset": TIMESTAMP_OFFSET,
        })
        return info

    def get_available_files(self) -> List[Dict]:
        return self.available_files

    def _timestamp_fields(self) -> Dict:
        now = datetime.now(MALAYSIA_TZ)
        return {
            "timestamp": now.isoformat(timespec="seconds"),
            "timestamp_display": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_timezone": TIMESTAMP_TIMEZONE,
            "timestamp_offset": TIMESTAMP_OFFSET,
        }

    def _find_feature_row(self, filename: str) -> pd.Series:
        lookup_name = _basename_any_path(filename).lower()
        lookup_full = _normalize_lookup_text(filename)
        matches = self.feature_bank[
            (self.feature_bank["File_lookup_name"] == lookup_name)
            | (self.feature_bank["File_lookup_full"] == lookup_full)
        ].copy()
        if matches.empty:
            raise FileNotFoundError(USER_FRIENDLY_NOT_FOUND)
        if "is_original" in matches.columns:
            matches = matches.sort_values("is_original", ascending=False)
        return matches.iloc[0]

    def _prepare_features(self, row: pd.Series) -> np.ndarray:
        missing = [c for c in self.mtff_feature_columns_384 if c not in row.index]
        if missing:
            raise ValueError(f"Feature bank is missing required MTFF features: {missing[:5]}")
        x384 = row[self.mtff_feature_columns_384].astype(float).values.reshape(1, -1).astype(np.float32)
        if x384.shape[1] != 384:
            raise ValueError("Expected 384 MTFF input features before derived features.")
        x_plus = build_mtff_plus_features(x384)
        x_scaled = self.scaler.transform(x_plus).astype(np.float32)
        return x_scaled[:, self.selected_feature_indices]

    def classify_by_filename(self, filename: str, input_mode: str) -> Dict:
        start = time.perf_counter()
        row = self._find_feature_row(filename)
        x = self._prepare_features(row)
        primary_prob = float(safe_binary_probability(self.primary_model, x)[0])
        gate_prob = float(safe_binary_probability(self.gate_model, x)[0])
        event_fall_prob = float(event_fall_probability(self.event_model, x, self.event_classes, self.fall_class_ids)[0])
        final_prob = float(combine_probabilities([primary_prob], [gate_prob], [event_fall_prob], self.alpha, self.beta)[0])
        pred_label_int = int(final_prob >= self.threshold)
        prediction_text = "Fall" if pred_label_int == 1 else "Non-Fall"
        risk_level = "HIGH" if pred_label_int == 1 and final_prob >= 0.80 else ("MEDIUM" if pred_label_int == 1 else "LOW")
        actual_label = int(row["Label"]) if "Label" in row.index and not pd.isna(row["Label"]) else None
        actual_event = str(row["Event"]) if "Event" in row.index and not pd.isna(row["Event"]) else None
        correct = bool(pred_label_int == actual_label) if actual_label is not None else None
        ts = self._timestamp_fields()
        processing_time = float(time.perf_counter() - start)
        file_name = str(row["File"])
        return {
            "id": str(uuid.uuid4()),
            **ts,
            "file_name": file_name,
            "filename": file_name,
            "prediction_label": prediction_text,
            "prediction_text": prediction_text,
            "classified_activity": prediction_text,
            "probability": final_prob,
            "primary_probability": primary_prob,
            "gate_probability": gate_prob,
            "event_fall_probability": event_fall_prob,
            "fall_confidence_percent": round(final_prob * 100.0, 2),
            "threshold": self.threshold,
            "alpha_gate": self.alpha,
            "beta_event": self.beta,
            "risk_level": risk_level,
            "model_name": "MTFF Event-Aware Veto",
            "display_model_name": "MTFF Event-Aware Veto",
            "feature_source": "MTFF_384_feature_bank",
            "display_feature_source": "FFT + STFT + CWT + derived features + event-aware veto",
            "processing_time_sec": round(processing_time, 4),
            "actual_label": actual_label,
            "actual_event": actual_event,
            "correct": correct,
            "input_mode": input_mode,
            "status": "completed",
        }
