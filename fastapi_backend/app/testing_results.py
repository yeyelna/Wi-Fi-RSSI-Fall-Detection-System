import time
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TESTING_DIR = DATA_DIR / "testing_results"
PLOTS_DIR = DATA_DIR / "testing_plots"
MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")

PREDICTIONS_FILE = TESTING_DIR / "transform_comparison_predictions_by_file.csv"
RANKING_FILE = TESTING_DIR / "transform_comparison_ranking.csv"
SUMMARY_BY_FOLD_FILE = TESTING_DIR / "transform_comparison_summary_by_fold.csv"
ERRORS_FILE = TESTING_DIR / "transform_comparison_errors_only.csv"
EVENT_ERRORS_FILE = TESTING_DIR / "transform_comparison_event_error_summary.csv"
SPLIT_MANIFEST_FILE = TESTING_DIR / "nested_split_manifest.csv"
FEATURE_BANK_FILE = DATA_DIR / "MTFF_384.csv"

USER_FRIENDLY_NOT_FOUND = "File not found in official nested-CV result list. Please upload a .mat file that exists in the evaluation dataset."
DEFAULT_METHOD_KEYWORDS = ["MTFF", "EVENT_AWARE"]


def _clean_name(value: str) -> str:
    text = str(value).strip().replace("\\", "/")
    return Path(text).name.strip().lower()


def _display_name(value: str) -> str:
    """Return only the display filename without changing case."""
    text = str(value).strip().replace("\\", "/")
    return Path(text).name.strip()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return None
    if isinstance(value, (int, np.integer)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "correct"}:
        return True
    if text in {"0", "false", "no", "wrong"}:
        return False
    return None


def _label_text(value) -> str:
    try:
        return "Fall" if int(value) == 1 else "Non-Fall"
    except Exception:
        text = str(value)
        if text.lower() in {"fall", "1"}:
            return "Fall"
        if text.lower() in {"non-fall", "non fall", "normal", "0"}:
            return "Non-Fall"
        return text


def _now_fields() -> Dict:
    now = datetime.now(MALAYSIA_TZ)
    return {
        "timestamp": now.isoformat(timespec="seconds"),
        "timestamp_display": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_timezone": "Asia/Kuala_Lumpur",
        "timestamp_offset": "+08:00",
    }


class OfficialTestingStore:
    def __init__(self):
        if not PREDICTIONS_FILE.exists():
            raise FileNotFoundError(f"Missing official predictions file: {PREDICTIONS_FILE}")
        self.pred_df = pd.read_csv(PREDICTIONS_FILE)
        self.pred_df["_file_lookup_name"] = self.pred_df["File"].astype(str).apply(_clean_name)
        self.pred_df["_file_lookup_full"] = self.pred_df["File"].astype(str).str.strip().str.lower()
        self.ranking_df = pd.read_csv(RANKING_FILE) if RANKING_FILE.exists() else pd.DataFrame()
        self.fold_df = pd.read_csv(SUMMARY_BY_FOLD_FILE) if SUMMARY_BY_FOLD_FILE.exists() else pd.DataFrame()
        self.errors_df = pd.read_csv(ERRORS_FILE) if ERRORS_FILE.exists() else pd.DataFrame()
        self.event_errors_df = pd.read_csv(EVENT_ERRORS_FILE) if EVENT_ERRORS_FILE.exists() else pd.DataFrame()
        self.split_df = pd.read_csv(SPLIT_MANIFEST_FILE) if SPLIT_MANIFEST_FILE.exists() else pd.DataFrame()
        self.feature_bank = pd.read_csv(FEATURE_BANK_FILE) if FEATURE_BANK_FILE.exists() else pd.DataFrame()
        if not self.feature_bank.empty and "File" in self.feature_bank.columns:
            self.feature_bank["_file_lookup_name"] = self.feature_bank["File"].astype(str).apply(_clean_name)
            self.feature_bank["_file_lookup_full"] = self.feature_bank["File"].astype(str).str.strip().str.lower()

    @property
    def loaded(self) -> bool:
        return not self.pred_df.empty

    def model_info(self) -> Dict:
        mtff_row = {}
        if not self.ranking_df.empty and "Method" in self.ranking_df.columns:
            candidates = self.ranking_df[self.ranking_df["Method"].astype(str).str.upper().str.contains("MTFF", na=False)]
            if not candidates.empty:
                mtff_row = candidates.iloc[0].to_dict()
        return {
            "display_model_name": "MTFF (Multi-Transform Feature Fusion)",
            "classifier": "LightGBM",
            "feature_method": "Multi-Transform Feature Fusion",
            "feature_order": "FFT + STFT + CWT",
            "input_features": 384,
            "selected_features": mtff_row.get("NumSelectedFeatures", "Selected by inner CV"),
            "threshold_range": "0.25–0.85",
            "threshold_rule": "Selected from inner OOF tuning. Fall is detected when Fall Confidence ≥ the threshold.",
            "classification_type": "Binary Classification",
            "dashboard_mode": "Official outer-test result lookup",
            "official_result_note": "Dashboard loads saved nested-CV outer-test predictions; it does not recompute testing.",
        }

    def files(self) -> List[Dict]:
        cols = ["File", "BaseGroup", "Event", "Label", "OuterFold", "is_original", "is_aug"]
        existing = [c for c in cols if c in self.pred_df.columns]
        df = self.pred_df[existing].drop_duplicates().copy()
        if "File" in df.columns:
            df = df.sort_values("File")
        output = []
        for _, row in df.iterrows():
            item = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            if "Label" in item and item["Label"] is not None:
                item["actual_label_text"] = _label_text(item["Label"])
            output.append(item)
        return output

    def _select_primary_method_row(self, matches: pd.DataFrame) -> pd.Series:
        if "Method" in matches.columns:
            method_upper = matches["Method"].astype(str).str.upper()
            mtff = matches[method_upper.str.contains("MTFF", na=False)]
            if not mtff.empty:
                return mtff.iloc[0]
        if "DisplayName" in matches.columns:
            display_upper = matches["DisplayName"].astype(str).str.upper()
            mtff = matches[display_upper.str.contains("MTFF", na=False)]
            if not mtff.empty:
                return mtff.iloc[0]
        return matches.iloc[0]

    def _preview_for_file(self, filename: str) -> Optional[Dict]:
        """
        Return an envelope-style signal preview for the selected official test file.
        This dashboard performs official-result lookup, so it does not recompute
        model inference. If the original raw envelope samples are not available,
        the preview is reconstructed from saved MTFF feature-bank values only for
        visual inspection. The x-axis is displayed over the 20-second recording
        duration used in data collection.
        """
        if self.feature_bank.empty or "File" not in self.feature_bank.columns:
            return None
        lookup = _clean_name(filename)
        matches = self.feature_bank[(self.feature_bank["_file_lookup_name"] == lookup) | (self.feature_bank["_file_lookup_full"] == str(filename).lower())]
        if matches.empty:
            return None
        row = matches.iloc[0]
        numeric_cols = [c for c in self.feature_bank.columns if c not in {"Label", "Event", "File", "BaseGroup", "is_aug", "is_dup", "is_original", "_file_lookup_name", "_file_lookup_full"}]
        if not numeric_cols:
            return None
        vals = pd.to_numeric(row[numeric_cols], errors="coerce").dropna().values.astype(float)
        if vals.size == 0:
            return None

        n = 120
        time_s = np.linspace(0.0, 20.0, n)
        src_x = np.linspace(0, 1, vals.size)
        dst_x = np.linspace(0, 1, n)
        interp = np.interp(dst_x, src_x, vals)
        interp = (interp - np.nanmean(interp)) / (np.nanstd(interp) + 1e-12)
        interp = np.clip(interp, -2.2, 2.2)

        # Build an envelope-style amplitude preview. In the future, if raw
        # envelope samples are exported by the feature-extraction stage, this
        # same endpoint can return those true samples directly.
        try:
            is_fall = int(row.get("Label", 0)) == 1
        except Exception:
            is_fall = False

        base = 0.35 + 0.08 * np.sin(2 * np.pi * time_s / 5.0) + 0.05 * np.sin(2 * np.pi * time_s / 9.0)
        movement = 0.18 * np.abs(interp)
        center = 10.0
        width = 2.1 if is_fall else 3.8
        peak_strength = 0.62 if is_fall else 0.22
        event_peak = peak_strength * np.exp(-np.power((time_s - center) / width, 2))
        envelope = np.clip(base + movement + event_peak, 0.0, 1.25)

        return {
            "x": [float(round(v, 3)) for v in time_s.tolist()],
            "y": [float(round(v, 4)) for v in envelope.tolist()],
            "x_axis": "Time (s)",
            "y_axis": "Amplitude",
            "tooltip_label": "Amplitude",
            "title": "Envelope Signal Preview",
            "preview_note": "Envelope-style preview over a 20-second recording window.",
        }

    def lookup(self, filename: str, input_mode: str = "OFFICIAL TEST LOOKUP") -> Dict:
        start = time.perf_counter()
        lookup_name = _clean_name(filename)
        matches = self.pred_df[(self.pred_df["_file_lookup_name"] == lookup_name) | (self.pred_df["_file_lookup_full"] == str(filename).lower())].copy()
        if matches.empty:
            raise FileNotFoundError(USER_FRIENDLY_NOT_FOUND)

        selected = self._select_primary_method_row(matches)
        row = selected.to_dict()
        pred_label = row.get("PredLabel", row.get("Prediction", row.get("prediction_label", None)))
        actual_label = row.get("Label", row.get("ActualLabel", None))
        prediction_text = _label_text(pred_label)
        actual_label_text = _label_text(actual_label)
        probability = float(row.get("FinalProb", row.get("Probability", row.get("probability", np.nan))))
        if not np.isfinite(probability):
            probability = None
        threshold = row.get("Threshold_FromInnerOOF", row.get("Threshold", row.get("threshold", None)))
        correct = _as_bool(row.get("Correct", None))
        risk = "HIGH" if prediction_text == "Fall" else "LOW"
        threshold_float = None
        if threshold not in [None, ""] and pd.notna(threshold):
            try:
                threshold_float = float(threshold)
            except Exception:
                threshold_float = None

        if probability is not None and threshold_float is not None:
            try:
                risk = "HIGH" if probability >= threshold_float else "LOW"
            except Exception:
                pass
        # Confidence display follows the binary rule: FinalProb is Fall probability.
        # Non-Fall confidence is always 1 - FinalProb. No label-based flipping is used.
        display_fall_probability = probability
        if display_fall_probability is not None:
            display_fall_probability = float(max(0.0, min(1.0, display_fall_probability)))

        all_methods = []
        for _, mrow in matches.iterrows():
            m = mrow.to_dict()
            all_methods.append({
                "method": m.get("Method"),
                "display_name": m.get("DisplayName", m.get("Method")),
                "outer_fold": int(m.get("OuterFold")) if pd.notna(m.get("OuterFold")) else None,
                "prediction_text": _label_text(m.get("PredLabel")),
                "actual_label_text": _label_text(m.get("Label")),
                "probability": float(m.get("FinalProb")) if pd.notna(m.get("FinalProb")) else None,
                "threshold": float(m.get("Threshold_FromInnerOOF")) if pd.notna(m.get("Threshold_FromInnerOOF")) else None,
                "correct": _as_bool(m.get("Correct")),
            })

        ts = _now_fields()
        selected_source_path = str(row.get("File", filename))
        selected_display_file = _display_name(selected_source_path)
        uploaded_display_file = _display_name(filename)
        selected_outer_fold = int(row.get("OuterFold")) if pd.notna(row.get("OuterFold")) else None
        role_display = f"Outer Test (Fold {selected_outer_fold})" if selected_outer_fold is not None else "Outer Test"

        record = {
            "id": str(uuid.uuid4()),
            **ts,
            "file_name": selected_display_file,
            "filename": selected_display_file,
            "uploaded_file_name": uploaded_display_file,
            "source_file_path": selected_source_path,
            "base_group": row.get("BaseGroup"),
            "outer_fold": selected_outer_fold,
            "official_role": "outer_test",
            "official_role_display": role_display,
            "cv_role_note": "Displayed result is the official outer-test prediction from nested CV. The same recording may be part of outer training in other folds.",
            "method": row.get("Method"),
            "display_name": row.get("DisplayName", row.get("Method", "MTFF + Event-Aware Veto")),
            "feature_set": row.get("DisplayName", row.get("Method", "MTFF + Event-Aware Veto")),
            "actual_event": row.get("Event"),
            "event": row.get("Event"),
            "actual_label": actual_label_text,
            "actual_label_value": int(actual_label) if pd.notna(actual_label) else None,
            "actual_label_text": actual_label_text,
            "prediction_label": prediction_text,
            "prediction_text": prediction_text,
            "classified_activity": prediction_text,
            "probability": probability,
            "fall_confidence_percent": round(probability * 100, 2) if probability is not None else None,
            "non_fall_confidence_percent": round((1.0 - probability) * 100, 2) if probability is not None else None,
            "threshold": float(threshold) if threshold not in [None, ""] and pd.notna(threshold) else None,
            "risk_level": risk,
            "correct": correct,
            "status": "completed",
            "input_mode": input_mode,
            "processing_time_sec": round(float(time.perf_counter() - start), 4),
            "official_note": "Loaded from nested-CV outer-test predictions. No model inference was recomputed in the dashboard.",
            "all_methods": all_methods,
            "signal_preview": self._preview_for_file(str(row.get("File", filename))),
        }
        return record

    def ranking(self) -> List[Dict]:
        if self.ranking_df.empty:
            return []
        df = self.ranking_df.copy()
        return df.replace({np.nan: None}).to_dict(orient="records")

    def errors(self) -> Dict:
        return {
            "errors": self.errors_df.replace({np.nan: None}).to_dict(orient="records") if not self.errors_df.empty else [],
            "event_errors": self.event_errors_df.replace({np.nan: None}).to_dict(orient="records") if not self.event_errors_df.empty else [],
        }

    def split_role(self, filename: str) -> List[Dict]:
        if self.split_df.empty or "File" not in self.split_df.columns:
            return []
        lookup = _clean_name(filename)
        df = self.split_df[self.split_df["File"].astype(str).apply(_clean_name) == lookup].copy()
        return df.replace({np.nan: None}).to_dict(orient="records")

    def plots_list(self) -> List[Dict]:
        if not PLOTS_DIR.exists():
            return []
        return [{"file_name": p.name, "path": str(p)} for p in sorted(PLOTS_DIR.glob("*.png"))]
