OLD INPUT PANEL REVERT + BACKEND FILENAME LOOKUP FIX
====================================================

This patch removes the new Search Prepared Dataset input panel by replacing streamlit_app/app.py
with the old input panel version:

- Enter Filename
- Classify by Filename
- Upload .mat File
- Upload and Classify

It also includes a fixed backend predictor.py that can match Windows-style paths in MTFF_384.csv
when running on Render/Linux. This makes typed filenames and uploaded prepared filenames such as
"data31.mat" match rows stored as full Windows paths.

FILES TO COPY
-------------
1) Copy this file into your repo:
   streamlit_app/app.py

2) If your backend is now inside fastapi_backend, copy:
   fastapi_backend/app/predictor.py

3) If your backend is still in the repo root, copy:
   app/predictor.py

IMPORTANT LIMITATION
--------------------
The upload panel can classify uploaded .mat files only by feature-bank lookup.
This means the uploaded filename must already exist inside data/MTFF_384.csv.
A totally new unseen .mat file requires the MATLAB/Python feature extraction step first,
because the backend model expects 384 MTFF features, not raw .mat data.

GIT COMMANDS
------------
cd /d "C:\Users\nurel\Downloads\ELLYANA FYP\Coding\Wi-Fi-RSSI-Fall-Detection-System"
git status
git add .
git commit -m "Restore old input panel and fix filename lookup"
git push origin main
