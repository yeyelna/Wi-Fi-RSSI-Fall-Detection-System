# Wi-Fi RSSI Fall Detection System — Upload-only Official Test Explorer

This Streamlit dashboard keeps the original visual template and layout. Users upload a `.mat` testing file. The backend uses the uploaded filename to load the official nested-CV outer-test result and reads variable `A` from the raw `.mat` file to display the extracted envelope signal preview.

Run the FastAPI backend first, then run this Streamlit app.
