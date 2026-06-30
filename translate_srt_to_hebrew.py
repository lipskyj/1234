#!/usr/bin/env python3
"""Translate an existing English subtitle file into Hebrew, keeping every
timestamp exactly as-is.

Use this when the video ALREADY has captions (e.g. Facebook/YouTube English
auto-captions you exported). It parses the timing of each cue, translates only
the text, and writes a Hebrew file with identical timings -- so each Hebrew
sentence appears at the right moment.

Accepts and emits ``.srt`` or ``.vtt``.

    pip install deep-translator        # online, no API key (recommended)
    python translate_srt_to_hebrew.py english.srt
    python translate_srt_to_hebrew.py english.srt -o hebrew.srt --bilingual

You can also paste plain text (one sentence per line, no timestamps) and this
script will still translate it -- it just won't have timings then. For that,
use --plain.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field


TS_RE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{3})"
)


@dataclass
class Cue:
    start: str
    end: str
    lines: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def parse_subtitles(text: str) -> list[Cue]:
    """Parse SRT or VTT content into cues (timestamps kept as raw strings)."""
    cues: list[Cue] = []
    current: Cue | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        m = TS_RE.search(line)
        if m:
            current = Cue(start=m.group(1), end=m.group(2))
            cues.append(current)
            continue
        if current is None:
            continue  # header / index lines before the first timestamp
        if line.strip() == "":
            current = None  # blank line ends the cue
            continue
        if line.strip().isdigit() and not current.lines:
            continue  # SRT numeric index that slipped through
        current.lines.append(line)
    return [c for c in cues if c.lines]


def parse_plain(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# --------------------------------------------------------------------------- #
# Translation
# --------------------------------------------------------------------------- #
def make_translator():
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        sys.exit(
            "error: needs deep-translator.\n"
            "       pip install deep-translator"
        )
    # 'iw' is Google's legacy code for Hebrew; deep-translator accepts 'iw'/'he'.
    return GoogleTranslator(source="en", target="iw")


def translate_lines(translator, lines: list[str]) -> list[str]:
    out = []
    for ln in lines:
        try:
            out.append(translator.translate(ln) or ln)
        except Exception as exc:  # noqa: BLE001
            print(f"war: failed to translate a line ({exc.__class__.__name__}); kept original",
                  file=sys.stderr)
            out.append(ln)
    return out


# --------------------------------------------------------------------------- #
# Writing
# --------------------------------------------------------------------------- #
def to_srt_ts(ts: str) -> str:
    return ts.replace(".", ",")


def to_vtt_ts(ts: str) -> str:
    return ts.replace(",", ".")


def write_srt(cues: list[Cue], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for i, c in enumerate(cues, 1):
            fh.write(f"{i}\n{to_srt_ts(c.start)} --> {to_srt_ts(c.end)}\n")
            fh.write("\n".join(c.lines) + "\n\n")


def write_vtt(cues: list[Cue], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("WEBVTT\n\n")
        for c in cues:
            fh.write(f"{to_vtt_ts(c.start)} --> {to_vtt_ts(c.end)}\n")
            fh.write("\n".join(c.lines) + "\n\n")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Translate an English .srt/.vtt to Hebrew, preserving timings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", help="path to the English .srt/.vtt (or .txt with --plain)")
    p.add_argument("-o", "--output", help="output path (default: <name>.he.<ext>)")
    p.add_argument("--bilingual", action="store_true",
                   help="keep the English line under the Hebrew one")
    p.add_argument("--plain", action="store_true",
                   help="input is plain text (one line per cue, no timestamps)")
    args = p.parse_args(argv)

    with open(args.input, encoding="utf-8-sig") as fh:
        content = fh.read()

    translator = make_translator()

    if args.plain:
        lines = parse_plain(content)
        hebrew = translate_lines(translator, lines)
        out = args.output or (os.path.splitext(args.input)[0] + ".he.txt")
        with open(out, "w", encoding="utf-8") as fh:
            for he, en in zip(hebrew, lines):
                fh.write((f"{he}\n{en}\n\n" if args.bilingual else f"{he}\n"))
        print(f"Done: {out}")
        return 0

    cues = parse_subtitles(content)
    if not cues:
        sys.exit("error: no timed cues found. Is this an .srt/.vtt? "
                 "For plain text use --plain.")
    print(f"parsed {len(cues)} cues; translating to Hebrew…")
    for c in cues:
        joined = " ".join(c.lines)
        he = translate_lines(translator, [joined])[0]
        c.lines = [he, joined] if args.bilingual else [he]

    ext = os.path.splitext(args.input)[1].lower()
    out = args.output or (os.path.splitext(args.input)[0] + ".he" + (ext or ".srt"))
    if out.lower().endswith(".vtt"):
        write_vtt(cues, out)
    else:
        write_srt(cues, out)
    print(f"Done: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
