#!/usr/bin/env python3
"""Deep Ocean Blue — Remotion render driver.

Builds ExplainerProps with typed cuts and invokes Remotion directly,
using the pre-installed Playwright headless_shell to avoid network download.
"""
import json
import sys
import os
import subprocess
import tempfile

sys.path.insert(0, '/home/user/1234')
os.chdir('/home/user/1234')

# --- Load and transform captions ---
caption_path = 'projects/deep-ocean-blue/assets/captions/narration.caption.json'
with open(caption_path) as f:
    caption_data = json.load(f)

word_captions = []
for cue in caption_data.get('cues', []):
    for w in cue.get('words', []):
        word_captions.append({
            'word': w['word'],
            'startMs': round(w['start'] * 1000),
            'endMs': round(w['end'] * 1000),
        })

print(f"Loaded {len(word_captions)} word captions")

# --- Dark ocean theme ---
theme_config = {
    'primaryColor': '#1a6fbf',
    'accentColor': '#4dabf7',
    'backgroundColor': '#040c18',
    'surfaceColor': '#0a1628',
    'textColor': '#e8f4fd',
    'mutedTextColor': '#8ab4d4',
    'headingFont': 'Inter',
    'bodyFont': 'Inter',
    'monoFont': 'JetBrains Mono',
    'chartColors': ['#2255FF', '#00BBCC', '#00BB55', '#FF8800', '#FF4400', '#FF0000'],
    'captionHighlightColor': '#4dabf7',
    'captionBackgroundColor': 'rgba(2, 8, 20, 0.85)',
    'springConfig': {'damping': 20, 'stiffness': 120, 'mass': 1},
    'transitionDuration': 0.4,
}

# --- Build ExplainerProps ---
composition_data = {
    'version': '1.0',
    'render_runtime': 'remotion',
    'renderer_family': 'explainer-data',
    'composition_mode': 'templated',
    'themeConfig': theme_config,
    'cuts': [
        # sc01 — Hook: depth descent (0–7s)
        {
            'id': 'cut-sc01',
            'source': '',
            'in_seconds': 0,
            'out_seconds': 7,
            'layer': 'primary',
            'type': 'text_card',
            'text': 'Dive into the ocean.\n\nRed is gone by 5m.\nOrange, at 25m.\nYellow, at 50m.',
            'transition_in': 'fade',
            'transition_out': 'cut',
            'transition_duration': 0.5,
            'backgroundColor': '#0a0f1a',
        },
        # sc02 — Setup: the question (7–14s)
        {
            'id': 'cut-sc02',
            'source': '',
            'in_seconds': 7,
            'out_seconds': 14,
            'layer': 'primary',
            'type': 'text_card',
            'text': "By 200 meters, only blue light remains.\n\nBut why?\nWhat's stripping each color away?",
            'transition_in': 'cut',
            'transition_out': 'dissolve',
            'transition_duration': 0.4,
            'backgroundColor': '#060c18',
        },
        # sc03 — Mechanism: O-H bond (14–23s)
        {
            'id': 'cut-sc03',
            'source': '',
            'in_seconds': 14,
            'out_seconds': 23,
            'layer': 'primary',
            'type': 'text_card',
            'text': 'Water absorbs light — but not equally.\n\nRed light excites O-H bonds.\nThe molecule vibrates.\nThe photon vanishes.',
            'transition_in': 'dissolve',
            'transition_out': 'cut',
            'transition_duration': 0.4,
            'backgroundColor': '#080c14',
        },
        # sc04 — Emotional beat (23–28s)
        {
            'id': 'cut-sc04',
            'source': '',
            'in_seconds': 23,
            'out_seconds': 28,
            'layer': 'primary',
            'type': 'text_card',
            'text': 'The molecule vibrates.\n\nThe photon vanishes.',
            'transition_in': 'cut',
            'transition_out': 'cut',
            'transition_duration': 0,
            'backgroundColor': '#060c18',
        },
        # sc05 — 50× hero stat (28–36s)
        {
            'id': 'cut-sc05',
            'source': '',
            'in_seconds': 28,
            'out_seconds': 36,
            'layer': 'primary',
            'type': 'stat_card',
            'stat': '50×',
            'subtitle': 'Red absorbed 50 times faster than blue',
            'transition_in': 'cut',
            'transition_out': 'cut',
            'transition_duration': 0,
            'backgroundColor': '#020814',
        },
        # sc06 — Absorption spectrum bar chart (36–43s)
        {
            'id': 'cut-sc06',
            'source': '',
            'in_seconds': 36,
            'out_seconds': 43,
            'layer': 'primary',
            'type': 'bar_chart',
            'title': 'Water Absorption Spectrum (m⁻¹)',
            'chartData': [
                {'label': '450nm Blue', 'value': 0.013},
                {'label': '500nm Cyan', 'value': 0.026},
                {'label': '550nm Green', 'value': 0.055},
                {'label': '600nm Orange', 'value': 0.245},
                {'label': '650nm Red-Org', 'value': 0.349},
                {'label': '700nm Red', 'value': 0.650},
            ],
            'chartColors': ['#2255FF', '#00BBCC', '#00BB55', '#FF8800', '#FF4400', '#FF0000'],
            'transition_in': 'cut',
            'transition_out': 'dissolve',
            'transition_duration': 0.5,
            'backgroundColor': '#040a16',
        },
        # sc07 — Scale reveal: 95% dark (43–54s)
        {
            'id': 'cut-sc07',
            'source': '',
            'in_seconds': 43,
            'out_seconds': 54,
            'layer': 'primary',
            'type': 'stat_card',
            'stat': '95%',
            'subtitle': 'of the ocean has zero sunlight',
            'transition_in': 'dissolve',
            'transition_out': 'dissolve',
            'transition_duration': 0.5,
            'backgroundColor': '#030810',
        },
        # sc08 — Closing (54–60s)
        {
            'id': 'cut-sc08',
            'source': '',
            'in_seconds': 54,
            'out_seconds': 60,
            'layer': 'primary',
            'type': 'text_card',
            'text': "The ocean's blue isn't reflected from the sky.\nIt's built into the water itself.\n\nBlue is simply what's left.",
            'transition_in': 'dissolve',
            'transition_out': 'fade',
            'transition_duration': 0.8,
            'backgroundColor': '#040c1a',
        },
    ],
    'captions': word_captions,
}

# --- Write props file ---
output_path = '/home/user/1234/projects/deep-ocean-blue/renders/deep-ocean-blue.mp4'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

props_path = '/tmp/claude-0/-home-user-1234/22e1a875-f4e7-5dba-8239-1d2b59043088/scratchpad/remotion_props.json'
with open(props_path, 'w', encoding='utf-8') as f:
    json.dump(composition_data, f)
print(f"Wrote props to {props_path}")

# --- Pre-installed headless shell (Playwright browser) ---
HEADLESS_SHELL = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell'
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

browser_path = HEADLESS_SHELL if os.path.exists(HEADLESS_SHELL) else CHROME
print(f"Using browser: {browser_path}")

composer_dir = '/home/user/1234/remotion-composer'

cmd = [
    'npx', 'remotion', 'render',
    'src/index.tsx',
    'Explainer',
    output_path,
    f'--props={props_path}',
    f'--browser-executable={browser_path}',
    '--ignore-certificate-errors',
    '--timeout=120000',
    '--log=verbose',
]

print(f"Running: {' '.join(cmd)}")
print()

result = subprocess.run(
    cmd,
    cwd=composer_dir,
    capture_output=False,
    timeout=540,
)

if result.returncode == 0:
    size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"\nSUCCESS — {output_path} ({size:,} bytes)")
else:
    print(f"\nFAILED — exit code {result.returncode}")
    sys.exit(result.returncode)
