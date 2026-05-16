from __future__ import annotations

import io
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd


def _normalize_basename(name: str) -> str:
    """Return a clean lowercase basename from any Windows/Linux path string."""
    return os.path.basename(str(name).replace("\\", "/")).strip().lower()


def _extract_data_mat_name(name: str) -> str:
    """
    Extract project-style filenames such as data60.mat from uploaded names.
    This fixes names like 20260516_xxxx_data60.mat.
    """
    raw = _normalize_basename(name)
    match = re.search(r"(data\d+(?:_aug\d+|_dup\d+)?\.mat)", raw, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return raw


@dataclass
class PredictionResult:
    prediction_label: int
    prediction_text: str
    probability: float
    threshold: float
    risk_level: str
    model_name: str
    feature_source: str
    processing_time_sec: float
    file_name: Optional[str] = None
    input_mode: str = "MANUAL TEST"
    actual_label: Optional[int] = None
    actual_event: Optional[str] = None
    correct: Optional[bool] = None
    feature_count_before_selection: int = 384
    selected_feature_count: int = 208


class WifiFallPredictor:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / "model_artifacts"
        self.data_dir = self.base_dir / "data"
        self.package_path = self.artifacts_dir / "balanced_comb_inference_package.pkl"
        self.feature_bank_path = self.data_dir / "COMB_Bal_384.csv"

        if not self.package_path.exists():
            raise FileNotFoundError(f"Missing inference package: {self.package_path}")
        if not self.feature_bank_path.exists():
            raise FileNotFoundError(f"Missing feature bank: {self.feature_bank_path}")

        package = joblib.load(self.package_path)
        self.model = package["model"]
        self.block_scalers = package.get("block_scalers", [])
        self.selected_feature_indices = [int(i) for i in package["selected_feature_indices"]]
        self.selected_feature_names = list(package["selected_feature_names"])
        self.all_feature_names_384 = list(package["all_feature_names_384"])
        self.threshold = float(package["threshold"])
        self.model_info = dict(package.get("model_info", {}))

        self.feature_bank = self._load_feature_bank()

    def _load_feature_bank(self) -> pd.DataFrame:
        df = pd.read_csv(self.feature_bank_path)
        missing = [c for c in self.all_feature_names_384 if c not in df.columns]
        if missing:
            raise ValueError(f"Feature bank is missing expected feature columns. First missing: {missing[:5]}")
        if "File" not in df.columns:
            raise ValueError("Feature bank must contain a File column.")
        df["__basename"] = df["File"].astype(str).map(_normalize_basename)
        return df

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "model_loaded": True,
            "feature_bank_loaded": True,
            "feature_bank_rows": int(len(self.feature_bank)),
            "model_name": self.model_info.get("model_name", "Balanced_COMB"),
        }

    def get_model_info(self) -> Dict[str, Any]:
        info = dict(self.model_info)
        info.update({
            "api_prediction_mode": "fast_feature_bank_lookup_for_mat_files",
            "feature_bank_rows": int(len(self.feature_bank)),
            "selected_feature_count_runtime": len(self.selected_feature_indices),
            "threshold_runtime": self.threshold,
        })
        return info

    def available_files(self, limit: int = 50, query: Optional[str] = None) -> Dict[str, Any]:
        sub = self.feature_bank
        if query:
            q = query.lower().strip()
            sub = sub[sub["__basename"].str.contains(q, na=False)]
        rows = []
        for _, row in sub.head(limit).iterrows():
            rows.append({
                "file_name": row["__basename"],
                "event": str(row.get("Event", "")),
                "label": int(row.get("Label")) if "Label" in row and pd.notna(row.get("Label")) else None,
            })
        return {"count": int(len(sub)), "items": rows}

    def _features_from_bank(self, file_name: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        lookup_name = _extract_data_mat_name(file_name)
        hits = self.feature_bank[self.feature_bank["__basename"] == lookup_name]

        if hits.empty:
            # As a fallback, try contains matching in case a prefix/suffix remains.
            raw = _normalize_basename(file_name)
            hits = self.feature_bank[self.feature_bank["__basename"].apply(lambda b: b in raw or raw in b)]

        if hits.empty:
            raise FileNotFoundError(
                f"{file_name} was not found in COMB_Bal_384.csv. "
                "For fast API mode, upload a .mat file that already exists in the feature bank, "
                "or upload a 384-feature CSV."
            )

        row = hits.iloc[0]
        x = row[self.all_feature_names_384].astype(float).to_numpy(dtype=np.float32).reshape(1, -1)
        meta = {
            "matched_file_name": row["__basename"],
            "actual_label": int(row["Label"]) if "Label" in row and pd.notna(row["Label"]) else None,
            "actual_event": str(row["Event"]) if "Event" in row and pd.notna(row["Event"]) else None,
        }
        return x, meta

    def _features_from_csv_bytes(self, content: bytes, file_name: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        df = pd.read_csv(io.BytesIO(content))
        missing = [c for c in self.all_feature_names_384 if c not in df.columns]
        if missing:
            # Support CSVs with only 384 unnamed/numeric columns plus optional File column.
            numeric = df.select_dtypes(include=[np.number])
            if numeric.shape[1] >= 384:
                x = numeric.iloc[0, :384].to_numpy(dtype=np.float32).reshape(1, -1)
            else:
                raise ValueError(
                    "CSV must contain the 384 MTFF feature columns or at least 384 numeric columns. "
                    f"Missing columns start with: {missing[:5]}"
                )
        else:
            x = df.loc[df.index[0], self.all_feature_names_384].astype(float).to_numpy(dtype=np.float32).reshape(1, -1)

        meta = {
            "matched_file_name": _normalize_basename(file_name),
            "actual_label": int(df.loc[df.index[0], "Label"]) if "Label" in df.columns and pd.notna(df.loc[df.index[0], "Label"]) else None,
            "actual_event": str(df.loc[df.index[0], "Event"]) if "Event" in df.columns and pd.notna(df.loc[df.index[0], "Event"]) else None,
        }
        return x, meta

    def _prepare_features(self, x384: np.ndarray) -> np.ndarray:
        if x384.shape != (1, 384):
            raise ValueError(f"Expected feature shape (1, 384), got {x384.shape}")
        x = x384.astype(np.float32).copy()

        # Apply the same block scalers saved from final trainval setup.
        for block in self.block_scalers:
            indices = [int(i) for i in block["indices"]]
            scaler = block["scaler"]
            x[:, indices] = scaler.transform(x[:, indices])

        selected = x[:, self.selected_feature_indices]
        return selected

    def _predict_from_x384(self, x384: np.ndarray, feature_source: str, meta: Dict[str, Any], file_name: Optional[str], input_mode: str = "MANUAL TEST") -> PredictionResult:
        t0 = time.perf_counter()
        x_selected = self._prepare_features(x384)
        prob = float(self.model.predict_proba(x_selected)[:, 1][0])
        pred = int(prob >= self.threshold)
        prediction_text = "Fall" if pred == 1 else "Non-Fall"

        if prob >= self.threshold:
            risk = "High"
        elif prob >= max(0.0, self.threshold - 0.15):
            risk = "Moderate"
        else:
            risk = "Low"

        actual_label = meta.get("actual_label")
        correct = None
        if actual_label is not None:
            correct = bool(pred == int(actual_label))

        return PredictionResult(
            prediction_label=pred,
            prediction_text=prediction_text,
            probability=prob,
            threshold=self.threshold,
            risk_level=risk,
            model_name=self.model_info.get("model_name", "Balanced_COMB"),
            feature_source=feature_source,
            processing_time_sec=round(time.perf_counter() - t0, 6),
            file_name=file_name or meta.get("matched_file_name"),
            input_mode=input_mode,
            actual_label=actual_label,
            actual_event=meta.get("actual_event"),
            correct=correct,
            feature_count_before_selection=384,
            selected_feature_count=len(self.selected_feature_indices),
        )

    def predict_by_filename(self, file_name: str) -> PredictionResult:
        x384, meta = self._features_from_bank(file_name)
        return self._predict_from_x384(x384, "precomputed_feature_bank", meta, file_name=meta.get("matched_file_name", file_name), input_mode="MANUAL TEST")

    def predict_upload(self, file_name: str, content: bytes) -> PredictionResult:
        clean = _normalize_basename(file_name)
        if clean.endswith(".csv"):
            x384, meta = self._features_from_csv_bytes(content, clean)
            return self._predict_from_x384(x384, "uploaded_feature_csv", meta, file_name=clean, input_mode="MANUAL UPLOAD")
        if clean.endswith(".mat"):
            # Fast mode: do not run MATLAB. Use filename to fetch exact existing features.
            x384, meta = self._features_from_bank(clean)
            return self._predict_from_x384(x384, "precomputed_feature_bank", meta, file_name=meta.get("matched_file_name", clean), input_mode="MANUAL UPLOAD")
        raise ValueError("Unsupported upload type. Please upload .mat or .csv only.")

    def predict_stream_features(self, features: List[float], source_name: str = "stream-window") -> PredictionResult:
        if len(features) != 384:
            raise ValueError(f"Expected 384 features, got {len(features)}")
        x384 = np.array(features, dtype=np.float32).reshape(1, 384)
        return self._predict_from_x384(x384, "stream_feature_vector", {}, file_name=source_name, input_mode="LIVE MONITORING")
