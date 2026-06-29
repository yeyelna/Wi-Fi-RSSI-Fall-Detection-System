# Deployment Notes

## Streamlit Cloud
Main file path:

```text
streamlit_app/app.py
```

The dashboard frontend calls the Render FastAPI backend:

```text
https://wi-fi-rssi-fall-detection-system.onrender.com
```

## Render FastAPI
Root Directory:

```text
fastapi_backend
```

Start Command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
