#!/usr/bin/env python3
"""Download videos from Kan Hinuchit, transcribe, save transcripts, and create quizzes."""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_CHANNEL_URL = "https://www.youtube.com/@KanHinuchit/videos"
QUESTION_COUNTS = (5, 10, 15, 20)


@dataclass
class VideoItem:
    video_id: str
    title: str
    url: str


class PipelineError(RuntimeError):
    """Pipeline specific error."""


def run_cmd(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise PipelineError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\-\. ]+", "_", name, flags=re.UNICODE).strip()[:140]


def fetch_all_videos(channel_url: str, limit: int | None = None) -> list[VideoItem]:
    cmd = [
        "yt-dlp",
        "--dump-single-json",
        "--flat-playlist",
        channel_url,
    ]
    payload = json.loads(run_cmd(cmd))
    entries = payload.get("entries", [])

    videos: list[VideoItem] = []
    for entry in entries[:limit] if limit else entries:
        video_id = entry.get("id")
        title = entry.get("title") or video_id
        if not video_id:
            continue
        url = f"https://www.youtube.com/watch?v={video_id}"
        videos.append(VideoItem(video_id=video_id, title=title, url=url))
    return videos


def download_audio(video: VideoItem, audio_dir: Path) -> Path:
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(audio_dir / f"{video.video_id}.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f",
        "bestaudio/best",
        "-o",
        output_template,
        "--extract-audio",
        "--audio-format",
        "mp3",
        video.url,
    ]
    run_cmd(cmd)
    target = audio_dir / f"{video.video_id}.mp3"
    if not target.exists():
        raise PipelineError(f"Audio file not found after download: {target}")
    return target


def transcribe_audio(audio_file: Path, transcripts_dir: Path, model: str) -> Path:
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3",
        "-m",
        "whisper",
        str(audio_file),
        "--language",
        "he",
        "--task",
        "transcribe",
        "--model",
        model,
        "--output_format",
        "txt",
        "--output_dir",
        str(transcripts_dir),
    ]
    run_cmd(cmd)
    output = transcripts_dir / f"{audio_file.stem}.txt"
    if not output.exists():
        raise PipelineError(f"Transcript not found: {output}")
    return output


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in chunks if len(c.strip().split()) >= 6]


def to_cloze(sentence: str) -> tuple[str, str] | None:
    words = sentence.split()
    candidates = [w for w in words if len(re.sub(r"[^\w\u0590-\u05FF]", "", w)) >= 4]
    if not candidates:
        return None
    answer = random.choice(candidates)
    question = sentence.replace(answer, "____", 1)
    return question, answer


def generate_quiz_questions(transcript_text: str, count: int) -> list[dict[str, str]]:
    sentences = split_sentences(transcript_text)
    random.shuffle(sentences)

    questions: list[dict[str, str]] = []
    for sentence in sentences:
        cloze = to_cloze(sentence)
        if not cloze:
            continue
        question, answer = cloze
        questions.append({"question": question, "answer": answer})
        if len(questions) >= count:
            break

    return questions


def save_quiz(video: VideoItem, quizzes_dir: Path, count: int, questions: Iterable[dict[str, str]]) -> Path:
    quizzes_dir.mkdir(parents=True, exist_ok=True)
    safe_title = sanitize_filename(video.title)
    output_file = quizzes_dir / f"{video.video_id}_{safe_title}_{count}.md"

    lines = [f"# Quiz: {video.title}", f"Source: {video.url}", f"Questions: {count}", ""]
    for idx, item in enumerate(questions, start=1):
        lines.append(f"{idx}. {item['question']}")
        lines.append(f"   - Answer: {item['answer']}")

    output_file.write_text("\n".join(lines), encoding="utf-8")
    return output_file


def process_video(video: VideoItem, output_root: Path, model: str) -> None:
    print(f"Processing: {video.title} ({video.url})")
    audio_file = download_audio(video, output_root / "audio")
    transcript_file = transcribe_audio(audio_file, output_root / "transcripts", model=model)
    transcript_text = transcript_file.read_text(encoding="utf-8")

    for count in QUESTION_COUNTS:
        questions = generate_quiz_questions(transcript_text, count)
        if len(questions) < count:
            print(
                f"  Warning: only generated {len(questions)} questions for {video.video_id} (requested {count})."
            )
        quiz_path = save_quiz(video, output_root / "quizzes", count, questions)
        print(f"  Saved quiz: {quiz_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Kan Hinuchit videos, transcribe Hebrew text, and generate quizzes."
    )
    parser.add_argument("--channel-url", default=DEFAULT_CHANNEL_URL, help="YouTube channel/videos URL")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of videos to process")
    parser.add_argument("--model", default="small", help="Whisper model size (tiny/base/small/medium/large)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    videos = fetch_all_videos(args.channel_url, limit=args.limit)
    if not videos:
        raise PipelineError("No videos found. Check channel URL.")

    print(f"Found {len(videos)} videos")
    for video in videos:
        process_video(video, output_root=output_root, model=args.model)

    print("Done.")


if __name__ == "__main__":
    main()
