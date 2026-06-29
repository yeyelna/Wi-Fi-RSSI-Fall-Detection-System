from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .database import (
    delete_all_records,
    delete_record,
    init_db,
    insert_record,
    latest_record,
    list_records,
)
from .testing_results import OfficialTestingStore, USER_FRIENDLY_NOT_FOUND
from .signal_preview import envelope_preview_from_mat_bytes

app = FastAPI(
    title="Wi-Fi RSSI Official Testing Result API",
    description="FastAPI backend that loads saved nested-CV outer-test predictions. It does not recompute testing.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = OfficialTestingStore()
init_db()



@app.get("/")
def root():
    return {
        "name": "Wi-Fi RSSI Official Testing Result API",
        "docs": "/docs",
        "health": "/health",
        "mode": "official_outer_test_lookup",
        "note": "This backend loads saved nested-CV outer-test predictions and does not recompute testing.",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "testing_results_loaded": store.loaded,
        "mode": "official_outer_test_lookup",
    }


@app.get("/model-info")
def model_info():
    return store.model_info()


@app.get("/testing/ranking")
def testing_ranking():
    return {"items": store.ranking()}


@app.get("/testing/files")
def testing_files():
    return {"items": store.files()}




@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    try:
        clean_name = Path(file.filename or "").name
        if Path(clean_name).suffix.lower() != ".mat":
            raise HTTPException(status_code=400, detail="Please upload a .mat file.")
        file_bytes = await file.read()
        record = store.lookup(clean_name, input_mode="OFFICIAL TEST UPLOAD LOOKUP")
        try:
            record["signal_preview"] = envelope_preview_from_mat_bytes(file_bytes, clean_name)
        except Exception as sig_exc:
            record["signal_preview"] = None
            record["signal_preview_error"] = str(sig_exc)
        insert_record(record)
        return record
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=USER_FRIENDLY_NOT_FOUND)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Testing lookup failed: {str(exc)}")


@app.get("/testing/split-role")
def testing_split_role(filename: str = Query(...)):
    return {"items": store.split_role(filename)}


@app.get("/testing/errors")
def testing_errors():
    return store.errors()


@app.get("/testing/plots-list")
def testing_plots_list():
    return {"items": store.plots_list()}


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
