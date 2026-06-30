#!/usr/bin/env python3
"""Generate Hebrew captions (.srt / .vtt) from a video or audio file.

Pipeline
--------
  1. (optional) download the video from a URL with yt-dlp (Facebook reels,
     YouTube, etc. -- only works for content the running machine can reach).
  2. transcribe the audio with OpenAI Whisper -- auto-detects the spoken
     language and produces per-segment timestamps.
  3. translate every segment into Hebrew.
  4. write a Hebrew ``.srt`` and ``.vtt`` (optionally bilingual: original +
     Hebrew stacked).

Why a script instead of doing it in the chat?
---------------------------------------------
Cloud agent sessions are frequently behind an egress policy that blocks
facebook.com / drive.google.com and the model-weight hosts, and they have no
audio-transcription capability. This tool is meant to run on the machine that
actually HAS the media file (e.g. your own PC), where none of those blocks
apply.

Quick start
-----------
    pip install -r requirements.txt
    # ffmpeg must be on PATH (https://ffmpeg.org/download.html)

    # from a local file:
    python generate_hebrew_captions.py "C:/Users/User/.../123.mp4"

    # from a URL (public video):
    python generate_hebrew_captions.py "https://www.facebook.com/reel/939150352070033"

    # bilingual subtitles, larger/more-accurate model:
    python generate_hebrew_captions.py video.mp4 --bilingual --model medium

Outputs ``<name>.he.srt`` and ``<name>.he.vtt`` next to the input.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Segment:
    """One caption cue."""
    start: float          # seconds
    end: float            # seconds
    text: str             # original-language text
    hebrew: str = ""      # Hebrew translation (filled in later)


# --------------------------------------------------------------------------- #
# Step 1 -- obtain a local media file
# --------------------------------------------------------------------------- #
def resolve_media(source: str, workdir: str) -> str:
    """Return a path to a local media file, downloading first if ``source``
    is a URL. Requires yt-dlp for URLs."""
    if not (source.startswith("http://") or source.startswith("https://")):
        if not os.path.exists(source):
            sys.exit(f"error: file not found: {source}")
        return source

    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        sys.exit(
            "error: downloading from a URL needs yt-dlp.\n"
            "       pip install yt-dlp   (and make sure the host is reachable)"
        )

    out_tmpl = os.path.join(workdir, "download.%(ext)s")
    ydl_opts = {
        "outtmpl": out_tmpl,
        "format": "bestaudio/best",
        "quiet": True,
        "noprogress": True,
    }
    print(f"[1/4] downloading: {source}")
    import yt_dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(source, download=True)
        path = ydl.prepare_filename(info)
    # prepare_filename may report the pre-merge extension; pick what exists.
    if not os.path.exists(path):
        base = os.path.splitext(path)[0]
        for ext in (".m4a", ".webm", ".mp4", ".mp3", ".opus", ".wav"):
            if os.path.exists(base + ext):
                path = base + ext
                break
    if not os.path.exists(path):
        sys.exit("error: download finished but no media file was produced")
    return path


# --------------------------------------------------------------------------- #
# Step 2 -- transcribe with Whisper
# --------------------------------------------------------------------------- #
def transcribe(media_path: str, model_name: str, language: str | None) -> tuple[list[Segment], str]:
    """Transcribe ``media_path`` with Whisper. Returns (segments, detected_lang)."""
    try:
        import whisper  # openai-whisper
    except ImportError:
        sys.exit(
            "error: transcription needs openai-whisper.\n"
            "       pip install -U openai-whisper   (and install ffmpeg)"
        )

    print(f"[2/4] transcribing with Whisper '{model_name}' (this can take a while)…")
    model = whisper.load_model(model_name)
    result = model.transcribe(
        media_path,
        language=language,          # None => auto-detect
        task="transcribe",          # keep source language; we translate ourselves
        verbose=False,
    )
    detected = result.get("language", language or "auto")
    segments = [
        Segment(start=float(s["start"]), end=float(s["end"]), text=s["text"].strip())
        for s in result.get("segments", [])
        if s["text"].strip()
    ]
    if not segments:
        sys.exit("error: Whisper produced no speech segments (silent or unsupported audio?)")
    print(f"      detected language: {detected} | {len(segments)} segments")
    return segments, detected


# --------------------------------------------------------------------------- #
# Step 3 -- translate each segment to Hebrew
# --------------------------------------------------------------------------- #
def translate_to_hebrew(segments: list[Segment], source_lang: str) -> None:
    """Fill ``Segment.hebrew`` in place.

    Tries, in order:
      1. deep-translator's GoogleTranslator (online, best quality, no key)
      2. argostranslate (fully offline, needs the <src>->he package installed)
    """
    print("[3/4] translating to Hebrew…")

    # --- attempt 1: deep-translator (online) ------------------------------- #
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="auto", target="iw")  # 'iw' == Hebrew
        for seg in segments:
            seg.hebrew = translator.translate(seg.text) or ""
        if any(s.hebrew for s in segments):
            print("      translated via Google (deep-translator)")
            return
    except Exception as exc:  # noqa: BLE001 -- fall through to offline path
        print(f"      online translation unavailable ({exc.__class__.__name__}); trying offline…")

    # --- attempt 2: argostranslate (offline) ------------------------------- #
    try:
        import argostranslate.translate as at
        langs = at.get_installed_languages()
        src = next((l for l in langs if l.code == (source_lang or "en")), None)
        heb = next((l for l in langs if l.code == "he"), None)
        if src and heb:
            tr = src.get_translation(heb)
            for seg in segments:
                seg.hebrew = tr.translate(seg.text)
            print("      translated via argostranslate (offline)")
            return
    except Exception:  # noqa: BLE001
        pass

    sys.exit(
        "error: could not translate to Hebrew.\n"
        "       install one of:\n"
        "         pip install deep-translator     # online, no API key\n"
        "         pip install argostranslate       # offline (then install the\n"
        "                                          #  <source>->he language pack)"
    )


# --------------------------------------------------------------------------- #
# Step 4 -- write subtitle files
# --------------------------------------------------------------------------- #
def _fmt_ts(seconds: float, vtt: bool = False) -> str:
    """Format seconds as an SRT (00:00:00,000) or VTT (00:00:00.000) timestamp."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    sep = "." if vtt else ","
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def _cue_text(seg: Segment, bilingual: bool) -> str:
    if bilingual and seg.text:
        return f"{seg.hebrew}\n{seg.text}"
    return seg.hebrew or seg.text


def write_srt(segments: list[Segment], path: str, bilingual: bool) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for i, seg in enumerate(segments, 1):
            fh.write(f"{i}\n")
            fh.write(f"{_fmt_ts(seg.start)} --> {_fmt_ts(seg.end)}\n")
            fh.write(_cue_text(seg, bilingual) + "\n\n")


def write_vtt(segments: list[Segment], path: str, bilingual: bool) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("WEBVTT\n\n")
        for seg in segments:
            fh.write(f"{_fmt_ts(seg.start, vtt=True)} --> {_fmt_ts(seg.end, vtt=True)}\n")
            fh.write(_cue_text(seg, bilingual) + "\n\n")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Generate Hebrew captions (.srt/.vtt) from a video/audio file or URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("source", help="path to a local video/audio file, or a video URL")
    p.add_argument("-o", "--output", help="output basename (default: alongside the input)")
    p.add_argument("--model", default="small",
                   help="Whisper model: tiny|base|small|medium|large (default: small)")
    p.add_argument("--language", default=None,
                   help="force source language code (e.g. en, ar, ru); default auto-detect")
    p.add_argument("--bilingual", action="store_true",
                   help="stack Hebrew over the original line in each cue")
    args = p.parse_args(argv)

    with tempfile.TemporaryDirectory() as workdir:
        media = resolve_media(args.source, workdir)
        segments, lang = transcribe(media, args.model, args.language)
        translate_to_hebrew(segments, lang)

        if args.output:
            base = args.output
        elif args.source.startswith(("http://", "https://")):
            base = os.path.join(os.getcwd(), "captions")
        else:
            base = os.path.splitext(args.source)[0]

        srt_path, vtt_path = base + ".he.srt", base + ".he.vtt"
        print("[4/4] writing subtitle files…")
        write_srt(segments, srt_path, args.bilingual)
        write_vtt(segments, vtt_path, args.bilingual)

    print(f"\nDone:\n  {srt_path}\n  {vtt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
