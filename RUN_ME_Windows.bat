@echo off
REM ====================================================================
REM  One-click Hebrew captions (Windows).
REM  1) Paste the English captions into english_captions.PASTE_HERE.txt
REM     (one sentence per line) and save it.
REM  2) Double-click this file.
REM  Result: english_captions.he.txt  (Hebrew, line-for-line)
REM  If you have a real .srt, name it english_captions.srt and this script
REM  will translate it WITH the timestamps instead.
REM ====================================================================
setlocal
cd /d "%~dp0"

echo Installing the translator (one time)...
python -m pip install --quiet --disable-pip-version-check deep-translator
if errorlevel 1 (
  echo.
  echo Could not install deep-translator. Is Python installed and on PATH?
  echo Download Python from https://www.python.org/downloads/ and re-run.
  pause
  exit /b 1
)

if exist "english_captions.srt" (
  echo Translating english_captions.srt  -- keeping timestamps...
  python translate_srt_to_hebrew.py "english_captions.srt"
) else if exist "english_captions.PASTE_HERE.txt" (
  echo Translating english_captions.PASTE_HERE.txt  -- plain text...
  python translate_srt_to_hebrew.py "english_captions.PASTE_HERE.txt" --plain -o "english_captions.he.txt"
) else (
  echo.
  echo No input found. Put your English captions in:
  echo   english_captions.PASTE_HERE.txt   ^(plain text^)  OR
  echo   english_captions.srt              ^(with timestamps^)
)

echo.
echo Done. Look for the .he.* file in this folder.
pause
