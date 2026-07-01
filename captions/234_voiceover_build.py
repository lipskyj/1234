# -*- coding: utf-8 -*-
# Offline Hebrew voiceover via espeak-ng Esperanto engine on phonetic transliteration.
import subprocess, wave, os
import numpy as np

SR = 22050
VDUR = 65.79

# (start, end, esperanto-phonetic transliteration of the Hebrew line)
cues = [
 (7.55, 8.83, "kama kveda kos hamajim hazot?"),
 (8.83, 10.47, "melisa, tirci laanot?"),
 (11.11, 12.15, "e,"),
 (12.15, 13.15, "matajim uŝloŝim gram."),
 (13.91, 14.79, "ŝloŝ meot vearbaim gram."),
 (16.91, 18.03, "arba meot vaĥamiŝim gram."),
 (19.67, 20.87, "hamiŝkal hamuĥlat"),
 (21.19, 22.51, "ŝel hakos lo meŝane."),
 (23.27, 24.95, "ze taluj kama zman ani maĥzik ota."),
 (25.83, 27.23, "im aĥzik ota daka, klum"),
 (27.23, 27.83, "lo kore."),
 (28.15, 29.87, "im aĥzik ota ŝaa, hajad ŝeli"),
 (29.87, 30.79, "tatĥil liĥov."),
 (31.51, 33.75, "im aĥzik ota jom ŝalem, hajad ŝeli"),
 (33.75, 35.51, "tihje keha umeŝuteket."),
 (35.99, 37.67, "hamiŝkal ŝel hakos lo"),
 (37.67, 39.35, "hiŝtana, aval keĥol ŝeani maĥzik ota joter,"),
 (39.35, 40.71, "kaĥ hi naasit kveda joter."),
 (42.07, 44.23, "halaĥacim vehadeagot ŝel haĥajim"),
 (44.23, 45.63, "hem kmo kos hamajim hazot."),
 (46.39, 47.71, "im ĥoŝvim alejhem kcat"),
 (47.71, 48.87, "zman, ejn ŝum beaja."),
 (50.15, 51.95, "ĥoŝvim alejhem kcat joter,"),
 (52.39, 53.35, "veze matĥil liĥov."),
 (54.63, 57.07, "ĥoŝvim alejhem kol hajom,"),
 (57.07, 59.35, "vetargiŝu meŝutakim, lo mesugalim laasot"),
 (59.35, 60.15, "klum."),
 (61.83, 63.03, "tamid ziĥru"),
 (64.03, 65.19, "lehaniaĥ et hakos."),
]

def read_wav(path):
    with wave.open(path, "rb") as w:
        n = w.getnframes(); sr = w.getframerate()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32)
        if w.getnchannels() == 2:
            a = a.reshape(-1, 2).mean(axis=1)
    return a, sr

track = np.zeros(int(VDUR * SR) + SR, dtype=np.float32)

for i, (st, en, txt) in enumerate(cues):
    raw = f"raw_{i}.wav"
    subprocess.run(["espeak-ng", "-v", "eo", "-s", "158", "-p", "35", "-w", raw, txt],
                   check=True, stderr=subprocess.DEVNULL)
    dur = os.path.getsize(raw)  # placeholder
    a, sr = read_wav(raw)
    clip_dur = len(a) / sr
    # slot until next cue start (or a tail for the last)
    nxt = cues[i+1][0] if i+1 < len(cues) else en + 1.4
    slot = max(0.35, nxt - st)
    # compress if the clip would overrun the slot (keeps sync), capped for intelligibility
    if clip_dur > slot * 0.98:
        tempo = min(clip_dur / (slot * 0.95), 1.8)
        fit = f"fit_{i}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw,
                        "-filter:a", f"atempo={tempo:.4f}", fit], check=True)
        a, sr = read_wav(fit)
    # place into the track
    pos = int(st * SR)
    end = min(pos + len(a), len(track))
    track[pos:end] += a[:end - pos]

# normalize to avoid clipping
peak = np.max(np.abs(track)) or 1.0
track = (track / peak) * 0.95 * 32767
track = track.astype(np.int16)
with wave.open("vo.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(track.tobytes())
print("wrote vo.wav, duration", len(track)/SR, "s")
