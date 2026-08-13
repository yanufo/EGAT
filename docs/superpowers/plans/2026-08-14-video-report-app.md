# Video Report App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit app that accepts MP4 and SRT pairs, generates a structured report, and keeps a searchable list of past report results.

**Architecture:** The app uses a single Streamlit entry point with a local JSON history store. Uploads are validated in Python, parsed into a report object, and then persisted for later review without requiring a database.

**Tech Stack:** Python, Streamlit, pandas, pytest

## Global Constraints

- Keep the app lightweight and local to the workspace.
- Accept one MP4 and one SRT upload per generated report.
- Persist generated reports in a JSON file under the project.
- Make the workflow easy to use in a single-page Streamlit interface.

---

### Task 1: Define report generation and persistence behavior

**Files:**
- Create: `src/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: uploaded `Path` objects for the video and subtitle files
- Produces: `generate_report(video_path, srt_path)`, `save_reports(reports, path)`, `load_reports(path)`

- [ ] **Step 1: Write the failing test**

```python
def test_generate_report_creates_expected_summary(tmp_path):
    video_path = tmp_path / "sample.mp4"
    srt_path = tmp_path / "sample.srt"
    video_path.write_bytes(b"fake-video-data")
    srt_path.write_text(
        "1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n"
        "2\n00:00:04,000 --> 00:00:06,000\nSecond line\n",
        encoding="utf-8",
    )

    report = generate_report(video_path, srt_path)

    assert report["video_name"] == "sample.mp4"
    assert report["subtitle_name"] == "sample.srt"
    assert report["subtitle_count"] == 2
    assert report["total_words"] == 4
    assert report["status"] == "ready"
    assert "report_id" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_app.py -q`
Expected: FAIL because `generate_report` and related helpers are not defined yet.

- [ ] **Step 3: Write minimal implementation**

```python
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def generate_report(video_path, srt_path):
    subtitles = parse_srt(srt_path)
    total_words = sum(len(item["text"].split()) for item in subtitles)
    return {
        "report_id": str(uuid4()),
        "video_name": video_path.name,
        "subtitle_name": srt_path.name,
        "subtitle_count": len(subtitles),
        "total_words": total_words,
        "status": "ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_app.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_app.py src/app.py
git commit -m "feat: add report generation logic"
```

### Task 2: Build the Streamlit UI and history list

**Files:**
- Modify: `src/app.py`

**Interfaces:**
- Consumes: generated report dictionaries and persisted JSON history
- Produces: interactive upload form, generated report display, and saved report list

- [ ] **Step 1: Implement upload form and history loading**

Add a Streamlit page with upload widgets for MP4 and SRT, a submit button, and a history panel.

- [ ] **Step 2: Save a generated report into a local JSON file**

Use `save_reports` with a writable project data directory and append to the existing history.

- [ ] **Step 3: Render the list of all previously generated reports**

Create a table or selectable list with `report_id`, file names, status, and timestamp.

- [ ] **Step 4: Verify the app starts successfully**

Run: `python -m streamlit run src/app.py --server.headless true --server.port 8501`
Expected: server starts and page loads without import errors.

### Task 3: Final polish and validation

**Files:**
- Modify: `requirements.txt`
- Optional: `README.md`

**Interfaces:**
- Consumes: project dependencies and user-facing instructions
- Produces: installable app and usage guidance

- [ ] **Step 1: Add required dependencies**

```txt
streamlit
pandas
pytest
```

- [ ] **Step 2: Run the full relevant verification**

Run: `pytest -q` and then launch the app in headless mode.
Expected: tests pass and the app starts without runtime errors.
