import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import app as app_module


def test_generate_report_creates_expected_summary(tmp_path):
    video_path = tmp_path / "sample.mp4"
    srt_path = tmp_path / "sample.srt"
    video_path.write_bytes(b"fake-video-data")
    srt_path.write_text(
        "1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n"
        "2\n00:00:04,000 --> 00:00:06,000\nSecond line\n",
        encoding="utf-8",
    )

    report = app_module.generate_report(video_path, srt_path)

    assert report["video_name"] == "sample.mp4"
    assert report["subtitle_name"] == "sample.srt"
    assert report["subtitle_count"] == 2
    assert report["total_words"] == 4
    assert report["status"] == "ready"
    assert "report_id" in report


def test_save_and_load_report_history(tmp_path):
    history_path = tmp_path / "reports.json"
    report = {
        "report_id": "r-1",
        "video_name": "demo.mp4",
        "subtitle_name": "demo.srt",
        "status": "ready",
        "created_at": "2026-08-14T00:00:00",
    }

    app_module.save_reports([report], history_path)
    loaded = app_module.load_reports(history_path)

    assert loaded == [report]
