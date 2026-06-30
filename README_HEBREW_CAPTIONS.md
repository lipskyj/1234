# Hebrew Captions Toolkit

Generate **Hebrew subtitles** for a video — either by translating the video's
existing English captions (keeping the original timing for every sentence), or
by transcribing the audio from scratch.

This exists because a video's content can't always be reached from a cloud
session (Facebook / Google Drive and the transcription model hosts are often
blocked by network policy, and the session has no audio capability). These
scripts run on **your own machine**, where the media file lives.

---

## Which script do I use?

| Situation | Script |
|---|---|
| The video **already has English captions** (you can export/copy the `.srt`/`.vtt` or the text) | `translate_srt_to_hebrew.py` ← **your case** |
| You have only the **video/audio file** and need captions from scratch | `generate_hebrew_captions.py` |

---

## Setup (once)

```bash
pip install -r requirements.txt
# For generate_hebrew_captions.py you also need ffmpeg on PATH:
#   https://ffmpeg.org/download.html
```

---

## Case A — translate existing English captions to Hebrew (preserves timing)

If you have the English subtitle file (`.srt` or `.vtt`):

```bash
python translate_srt_to_hebrew.py english.srt
#   -> english.he.srt   (Hebrew text, identical timestamps)

python translate_srt_to_hebrew.py english.srt --bilingual
#   -> Hebrew on top, English underneath in each cue
```

If you only have the **plain text** of the captions (one sentence per line, no
timestamps):

```bash
python translate_srt_to_hebrew.py captions.txt --plain
#   -> captions.he.txt
```

### How to get the English `.srt` from a Facebook reel
1. Open the reel, turn on **CC** (captions).
2. Facebook auto-captions can be downloaded via the reel's caption settings, or
   copy the visible caption text line by line into a `.txt` and use `--plain`.

---

## Case B — make captions from the video itself

```bash
# from a local file (auto-detects the spoken language):
python generate_hebrew_captions.py "C:/Users/User/.../123.mp4"

# from a public URL:
python generate_hebrew_captions.py "https://www.facebook.com/reel/939150352070033"

# more accurate (slower) model + bilingual output:
python generate_hebrew_captions.py video.mp4 --model medium --bilingual
```

Outputs `*.he.srt` and `*.he.vtt` next to the input.

---

## Notes
- Hebrew is right-to-left; most players render the `.srt`/`.vtt` correctly. If a
  player misorders punctuation, enable its RTL/bidi option.
- `deep-translator` uses Google Translate (no API key) and needs internet.
  `argostranslate` is a fully-offline alternative.
- Whisper model sizes: `tiny` < `base` < `small` < `medium` < `large`
  (bigger = more accurate, slower, more RAM).
