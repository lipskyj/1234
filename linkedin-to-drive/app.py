"""Local web app: paste a LinkedIn video post link, get it saved to Google Drive."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

from drive_uploader import upload_file
from extractor import LinkedInExtractionError, extract_video

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process():
    data = request.get_json(silent=True) or {}
    post_url = (data.get("url") or "").strip()

    if not post_url:
        return jsonify({"error": "Paste a LinkedIn post URL first."}), 400
    if "linkedin.com" not in post_url:
        return jsonify({"error": "That doesn't look like a LinkedIn URL."}), 400

    try:
        video_url, title = extract_video(post_url)
    except LinkedInExtractionError as exc:
        return jsonify({"error": str(exc)}), 422

    safe_name = re.sub(r"[^\w\-. ]", "_", title).strip("_ ")[:80] or "linkedin_video"
    tmp_dir = Path(tempfile.mkdtemp(prefix="li2drive_"))
    local_path = tmp_dir / f"{safe_name}.mp4"

    try:
        _download(video_url, local_path)
        drive_link = upload_file(local_path, f"{safe_name}.mp4")
    except Exception as exc:  # surfaced to the UI as a plain error message
        return jsonify({"error": f"Failed: {exc}"}), 500
    finally:
        local_path.unlink(missing_ok=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return jsonify({"driveLink": drive_link, "fileName": f"{safe_name}.mp4"})


def _download(video_url: str, dest: Path) -> None:
    if video_url.endswith(".m3u8"):
        _download_via_ffmpeg(video_url, dest)
        return

    headers = {"User-Agent": "Mozilla/5.0"}
    with requests.get(video_url, headers=headers, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)


def _download_via_ffmpeg(video_url: str, dest: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "This video is an adaptive stream and needs ffmpeg to download. "
            "Install ffmpeg and try again."
        )
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_url, "-c", "copy", str(dest)],
        check=True,
        capture_output=True,
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
