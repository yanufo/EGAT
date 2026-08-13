# Video Report Generator

This project provides a Streamlit app for uploading an MP4 video and an SRT subtitle file, generating a basic report summary, and tracking all generated reports in a local history list.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run src/app.py
```

## Features

- Upload an MP4 video file
- Upload a matching SRT subtitle file
- Generate a structured report summary
- Save report history locally as JSON
- Review prior reports from the app history list
