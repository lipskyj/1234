# Kan Hinuchit Video Transcription + Quiz Generator

This project provides an end-to-end pipeline that:

1. Pulls **all videos** (or a limited subset) from כאן חינוכית (Kan Hinuchit) YouTube page.
2. Downloads audio per video.
3. Transcribes Hebrew speech into text files.
4. Automatically generates quizzes of **5 / 10 / 15 / 20** questions from each transcript.

## Requirements

- Python 3.10+
- `ffmpeg`
- `yt-dlp`
- `openai-whisper`

Install tools:

```bash
pip install yt-dlp openai-whisper
```

On Linux, install ffmpeg (example):

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Usage

Process all videos from Kan Hinuchit:

```bash
python3 kan_hinuchit_pipeline.py
```

Process only first 3 videos (quick test):

```bash
python3 kan_hinuchit_pipeline.py --limit 3 --model tiny
```

Use a different channel/videos URL:

```bash
python3 kan_hinuchit_pipeline.py --channel-url "https://www.youtube.com/@KanHinuchit/videos"
```

## Output structure

After running, files are written to `output/`:

- `output/audio/*.mp3` – extracted audio files.
- `output/transcripts/*.txt` – Hebrew transcript text per video.
- `output/quizzes/*_5.md`, `*_10.md`, `*_15.md`, `*_20.md` – quizzes for each transcript.

## Notes

- Quiz quality depends on transcript quality.
- If transcripts are short, fewer questions may be generated than requested.
- For large channels, runtime can be long.
