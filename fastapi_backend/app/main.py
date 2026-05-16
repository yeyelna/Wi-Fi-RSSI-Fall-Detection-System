from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .database import PredictionLogDB, derive_status
from .predictor import WifiFallPredictor

BASE_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(
    title="Wi-Fi RSSI Fall Detection API",
    description="FastAPI backend for MTFF + Balanced_COMB LightGBM fall detection. Fast .mat classification uses COMB_Bal_384 feature-bank lookup.",
    version="2.2-malaysia-time-history",
)

# Allows Figma Site / local React / Streamlit / browser code layers to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = WifiFallPredictor(BASE_DIR)
db = PredictionLogDB(BASE_DIR / "data" / "prediction_logs.db")


class FilenameRequest(BaseModel):
    filename: str = Field(..., examples=["data60.mat"])


class StreamFeaturesRequest(BaseModel):
    features: List[float] = Field(..., description="One 384-feature MTFF vector in FFT_128 + STFT_128 + CWT_128 order")
    source_name: str = "stream-window"


@app.get("/")
def root():
    return {
        "name": "Wi-Fi RSSI Fall Detection API",
        "docs": "/docs",
        "health": "/health",
        "classification_mode": "fast_feature_bank_lookup_for_mat_files",
        "timestamp_timezone": "Asia/Kuala_Lumpur",
        "timestamp_gmt_offset": "+08:00",
        "history_delete_endpoints": [
            "DELETE /history/{record_id}",
            "DELETE /history/manual",
            "DELETE /history/all",
        ],
    }


@app.get("/health")
def health():
    return predictor.health()


@app.get("/model-info")
def model_info():
    info = predictor.get_model_info()
    # UI-friendly display aliases. Internal model files still use Balanced_COMB.
    info["display_model_name"] = "MTFF"
    info["display_feature_order"] = "FFT + STFT + CWT"
    info["classification_type"] = "Binary Classification"
    info["timestamp_timezone"] = "Asia/Kuala_Lumpur"
    info["timestamp_gmt_offset"] = "+08:00"
    info["internal_model_name"] = info.get("model_name", "Balanced_COMB")
    return info


@app.get("/available-files")
def available_files(limit: int = Query(50, ge=1, le=200), query: Optional[str] = None):
    return predictor.available_files(limit=limit, query=query)


@app.post("/predict/by-filename")
def predict_by_filename(request: FilenameRequest):
    try:
        result = predictor.predict_by_filename(request.filename)
        payload = result.__dict__
        payload["input_mode"] = "MANUAL TEST"
        saved = db.insert(payload.copy())
        return saved
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = predictor.predict_upload(file.filename or "uploaded_file", content)
        payload = result.__dict__
        payload["input_mode"] = "MANUAL UPLOAD"
        saved = db.insert(payload.copy())
        return saved
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/predict/stream")
def predict_stream(request: StreamFeaturesRequest):
    try:
        result = predictor.predict_stream_features(request.features, source_name=request.source_name)
        payload = result.__dict__
        payload["input_mode"] = "LIVE MONITORING"
        saved = db.insert(payload.copy())
        return saved
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/latest-status")
def latest_status():
    latest = db.latest()
    if latest is None:
        return {"status": "no_classifications_yet"}
    return latest


@app.get("/history")
def history(limit: int = Query(20, ge=1, le=200)):
    items = db.history(limit=limit)
    return {"items": items, "records": items, "history": items}


@app.delete("/history/{record_id}")
def delete_history_record(record_id: int):
    result = db.delete_one(record_id)
    if result["deleted"] == 0:
        raise HTTPException(status_code=404, detail=f"No history record found with id={record_id}")
    return result


@app.delete("/history/manual")
def clear_manual_history():
    """Delete only MANUAL TEST and MANUAL UPLOAD records. Keep LIVE MONITORING records."""
    return db.clear_manual()


@app.delete("/history/all")
def clear_all_history(confirm: bool = Query(False, description="Set confirm=true to clear all history records.")):
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to clear all history records.")
    return db.clear_all()
