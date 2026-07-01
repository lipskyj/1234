#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Hebrew dub of video 234 using ElevenLabs TTS — run this on YOUR machine
(ElevenLabs is reachable from your computer; it is blocked in the Claude Code
web environment, which is why this is a local script).

Reproduces the same pipeline used for the captions: professor = male voice,
Melissa/students = female voice, each line time-aligned to its caption cue,
English audio removed (full dub). The Hebrew subtitles are already burned into
the input video (234_hebrew.mp4), so the output has captions + dubbed audio.

REQUIREMENTS
    pip install numpy requests
    ffmpeg on PATH

SETUP
    export ELEVENLABS_API_KEY=sk_your_key_here
    # Optional: pick voices from https://elevenlabs.io/app/voice-library
    export EL_VOICE_MALE=pNInz6obpgDQGcFmaJgB     # default: "Adam"
    export EL_VOICE_FEMALE=21m00Tcm4TlvDq8ikWAM   # default: "Rachel"

RUN
    python3 234_elevenlabs_dub.py 234_hebrew.mp4 234_hebrew_dub.mp4
"""
import os, sys, subprocess, wave, tempfile
import numpy as np
import requests

SR = 22050
API_KEY = os.environ["ELEVENLABS_API_KEY"]
V_MALE   = os.environ.get("EL_VOICE_MALE",   "pNInz6obpgDQGcFmaJgB")
V_FEMALE = os.environ.get("EL_VOICE_FEMALE", "21m00Tcm4TlvDq8ikWAM")
MODEL    = os.environ.get("EL_MODEL", "eleven_multilingual_v2")

# (start, end, hebrew_text, speaker)  speaker: 'm' professor, 'f' Melissa/students
CUES = [
 (7.55, 8.83,  "כמה כבדה כוס המים הזאת?", "m"),
 (8.83, 10.47, "מליסה, תרצי לענות?", "m"),
 (11.11,12.15, "אֶה,", "f"),
 (12.15,13.15, "230 גרם.", "f"),
 (13.91,14.79, "340 גרם.", "f"),
 (16.91,18.03, "450 גרם.", "f"),
 (19.67,20.87, "המשקל המוחלט", "m"),
 (21.19,22.51, "של הכוס לא משנה.", "m"),
 (23.27,24.95, "זה תלוי כמה זמן אני מחזיק אותה.", "m"),
 (25.83,27.23, "אם אחזיק אותה דקה, כלום", "m"),
 (27.23,27.83, "לא קורה.", "m"),
 (28.15,29.87, "אם אחזיק אותה שעה, היד שלי", "m"),
 (29.87,30.79, "תתחיל לכאוב.", "m"),
 (31.51,33.75, "אם אחזיק אותה יום שלם, היד שלי", "m"),
 (33.75,35.51, "תהיה קהה ומשותקת.", "m"),
 (35.99,37.67, "המשקל של הכוס לא", "m"),
 (37.67,39.35, "השתנה, אבל ככל שאני מחזיק אותה יותר,", "m"),
 (39.35,40.71, "כך היא נעשית כבדה יותר.", "m"),
 (42.07,44.23, "הלחצים והדאגות של החיים", "m"),
 (44.23,45.63, "הם כמו כוס המים הזאת.", "m"),
 (46.39,47.71, "אם חושבים עליהם קצת", "m"),
 (47.71,48.87, "זמן, אין שום בעיה.", "m"),
 (50.15,51.95, "חושבים עליהם קצת יותר,", "m"),
 (52.39,53.35, "וזה מתחיל לכאוב.", "m"),
 (54.63,57.07, "חושבים עליהם כל היום,", "m"),
 (57.07,59.35, "ותרגישו משותקים, לא מסוגלים לעשות", "m"),
 (59.35,60.15, "כלום.", "m"),
 (61.83,63.03, "תמיד זכרו", "m"),
 (64.03,65.19, "להניח את הכוס.", "m"),
]

def tts(text, voice):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    r = requests.post(url, headers={"xi-api-key": API_KEY, "accept": "audio/mpeg"},
                      json={"text": text, "model_id": MODEL,
                            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}})
    r.raise_for_status()
    return r.content

def to_wav(mp3_bytes):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(mp3_bytes); mp3 = f.name
    wav = mp3 + ".wav"
    subprocess.run(["ffmpeg","-v","error","-y","-i",mp3,"-ar",str(SR),"-ac","1",wav], check=True)
    return wav

def read_wav(p):
    with wave.open(p,"rb") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    return a

def atempo(wav, factor):
    out = wav + f".t.wav"
    subprocess.run(["ffmpeg","-v","error","-y","-i",wav,"-filter:a",f"atempo={factor:.4f}",out], check=True)
    return out

def main():
    src, dst = sys.argv[1], sys.argv[2]
    dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
                                         "-of","default=nk=1:noprint_wrappers=1",src]).strip())
    track = np.zeros(int(dur*SR)+SR, dtype=np.float32)
    for i,(st,en,text,spk) in enumerate(CUES):
        voice = V_MALE if spk=="m" else V_FEMALE
        wav = to_wav(tts(text, voice))
        a = read_wav(wav); clip = len(a)/SR
        nxt = CUES[i+1][0] if i+1 < len(CUES) else en+1.4
        slot = max(0.35, nxt-st)
        if clip > slot*0.98:
            a = read_wav(atempo(wav, min(clip/(slot*0.95), 1.8)))
        pos = int(st*SR); end = min(pos+len(a), len(track))
        track[pos:end] += a[:end-pos]
        print(f"[{i+1}/{len(CUES)}] {spk} {text}")
    peak = np.max(np.abs(track)) or 1.0
    track = (track/peak*0.95*32767).astype(np.int16)
    vo = "vo_el.wav"
    with wave.open(vo,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(track.tobytes())
    # full dub: replace audio entirely with the Hebrew VO
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-i",vo,
                    "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k",
                    "-shortest","-movflags","+faststart",dst], check=True)
    print("wrote", dst)

if __name__ == "__main__":
    main()
