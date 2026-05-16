# Wi-Fi RSSI Fall Detection FastAPI Backend

Version: 2.2 Malaysia Time + frontend-friendly history

This API provides fast classification for the Wi-Fi RSSI fall detection dashboard.
It uses the pre-extracted MTFF feature bank (`COMB_Bal_384.csv`) and the saved Balanced_COMB/MTFF LightGBM inference package.

## Main updates in v2.2

- Timestamps are saved using Malaysia time: `Asia/Kuala_Lumpur`, GMT/UTC+8.
- Prediction responses now include `id`, `timestamp`, and `status`.
- `/history` returns records under `items`, `records`, and `history` to make frontend integration easier.
- Each history record includes frontend-friendly aliases such as:
  - `filename`
  - `classified_activity`
  - `fall_confidence`
  - `fall_confidence_percent`
  - `display_model_name`
  - `display_feature_source`
  - `status`
- History delete endpoints are included.

## Run

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Useful endpoints

- `GET /health`
- `GET /model-info`
- `GET /available-files`
- `POST /predict/by-filename`
- `POST /predict/batch`
- `POST /predict/stream`
- `GET /latest-status`
- `GET /history`
- `DELETE /history/{record_id}`
- `DELETE /history/manual`
- `DELETE /history/all?confirm=true`

## History record format

`GET /history` returns:

```json
{
  "items": [...],
  "records": [...],
  "history": [...]
}
```

Each record includes Malaysia timestamp with `+08:00` offset.
