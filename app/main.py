from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import (
    delete_all_records,
    delete_manual_records,
    delete_record,
    init_db,
    insert_record,
    latest_record,
    list_records,
)
from .predictor import MTFFPredictor, USER_FRIENDLY_NOT_FOUND

app = FastAPI(
    title="Wi-Fi RSSI Fall Detection API",
    description="FastAPI backend for MTFF event-aware veto Wi-Fi RSSI fall detection.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = MTFFPredictor()
init_db()


class FilenameRequest(BaseModel):
    filename: str


class StreamRequest(BaseModel):
    filename: Optional[str] = None


@app.get("/")
def root():
    return {
        "name": "Wi-Fi RSSI Fall Detection API",
        "docs": "/docs",
        "health": "/health",
        "classification_mode": "mtff_event_aware_veto_feature_lookup",
        "timestamp_timezone": "Asia/Kuala_Lumpur",
        "timestamp_gmt_offset": "+08:00",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": predictor.model_loaded,
        "feature_bank_loaded": predictor.feature_bank_loaded,
    }


@app.get("/model-info")
def model_info():
    return predictor.get_model_info()


@app.get("/available-files")
def available_files():
    return predictor.get_available_files()


@app.post("/predict/by-filename")
def predict_by_filename(payload: FilenameRequest):
    try:
        record = predictor.classify_by_filename(payload.filename, input_mode="MANUAL TEST")
        insert_record(record)
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=USER_FRIENDLY_NOT_FOUND)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(exc)}")


@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    try:
        clean_name = Path(file.filename).name
        record = predictor.classify_by_filename(clean_name, input_mode="MANUAL UPLOAD")
        insert_record(record)
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=USER_FRIENDLY_NOT_FOUND)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(exc)}")


@app.post("/predict/stream")
def predict_stream(payload: Optional[StreamRequest] = Body(default=None)):
    if payload is None or not payload.filename:
        latest = latest_record()
        return {
            "status": "ready",
            "message": "Provide a filename from the prepared dataset to simulate live monitoring.",
            "input_mode": "LIVE MONITORING",
            "latest_record": latest,
        }
    try:
        record = predictor.classify_by_filename(payload.filename, input_mode="LIVE MONITORING")
        insert_record(record)
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=USER_FRIENDLY_NOT_FOUND)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(exc)}")


@app.get("/latest-status")
def latest_status():
    latest = latest_record()
    if latest is None:
        return {"status": "no_history", "record": None}
    return latest


@app.get("/history")
def history(limit: int = Query(default=20, ge=1, le=500)):
    records = list_records(limit=limit)
    return {"items": records, "records": records, "history": records}


@app.delete("/history/manual")
def delete_manual_history():
    count = delete_manual_records()
    return {"status": "ok", "deleted_records": count}


@app.delete("/history/all")
def delete_all_history(confirm: bool = Query(default=False)):
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to delete all history records.")
    count = delete_all_records()
    return {"status": "ok", "deleted_records": count}


@app.delete("/history/{record_id}")
def delete_one_history_record(record_id: str):
    deleted = delete_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History record not found.")
    return {"status": "ok", "deleted_record_id": record_id}
