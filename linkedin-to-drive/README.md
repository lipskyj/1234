# LinkedIn Video → Google Drive

A tiny local web app: paste a LinkedIn post URL, click a button, and the
video in that post is downloaded and uploaded straight to your Google
Drive.

> **Use responsibly.** This only works for videos you're allowed to view
> (public posts, or your own posts / posts shared with you). LinkedIn's
> markup isn't a stable public API, so extraction may break if they
> change their page structure, and their Terms of Service restrict
> automated scraping — use this for personal archival of content you
> have the right to save, not for bulk downloading other people's posts.

## Quickstart on Windows (no typing commands)

1. Download this project: on GitHub click the green **Code** button →
   **Download ZIP**, then right-click the ZIP → **Extract All**.
2. Open the extracted `linkedin-to-drive` folder.
3. Before your first real download, do the one-time
   **[Create a Google OAuth client](#create-a-google-oauth-client-one-time)**
   step below — it's a few clicks in your browser, no coding.
4. Double-click **`run_windows.bat`**. The first time, it installs
   everything it needs automatically (this can take a minute), then
   opens the app in your browser.
5. Paste a LinkedIn post link and click the button. Leave the black
   window open while it's working — that's the app running.

If Windows shows a blue "Windows protected your PC" popup the first
time you run it, click **More info** → **Run anyway** (this happens for
any script downloaded from the internet, it's not a virus warning
specific to this).

If Python isn't installed yet, the script will tell you and point you
to the download page — install it, then double-click `run_windows.bat`
again.

## Manual install (Mac/Linux, or if you prefer the terminal)

```bash
cd linkedin-to-drive
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

Optional: install [ffmpeg](https://ffmpeg.org/download.html) and make
sure it's on your PATH. Only needed for the rare post whose video is
served as an adaptive `.m3u8` stream instead of a plain `.mp4`.

## Create a Google OAuth client (one-time)

This is what lets the app save files to *your* Drive — it's a
one-time setup, about 5 minutes:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
   and sign in with your Google account.
2. At the top, click the project dropdown → **New Project**. Give it
   any name (e.g. "linkedin-to-drive") → **Create**. Wait for it to
   finish, then make sure it's selected in that same dropdown.
3. In the search bar at the top, type **Google Drive API**, click it,
   then click the blue **Enable** button.
4. In the left sidebar, go to **APIs & Services → Credentials**.
5. Click **Create Credentials** → **OAuth client ID**.
   - If asked to configure a consent screen first: choose **External**,
     fill in an app name and your email in the required fields, save
     through the remaining steps with the defaults. Then come back and
     click **Create Credentials → OAuth client ID** again.
   - Application type: **Desktop app**. Give it any name.
   - Click **Create**.
6. A popup shows your client info — click **Download JSON**.
7. Rename that downloaded file to exactly `credentials.json` and move
   it into the `linkedin-to-drive` folder (next to `app.py`).

The app only requests the `drive.file` scope, so it can only see/manage
files it creates itself — not your whole Drive.

## Run it

Windows: double-click `run_windows.bat` (see Quickstart above).

Mac/Linux/manual: `python app.py`, then open
http://127.0.0.1:5000 in your browser.

Paste a LinkedIn post link and click **Download & upload to Drive**.
The first time you upload, a browser tab opens asking you to sign in
to Google and approve access — after that, a `token.json` is cached
locally so you won't be asked again.

## Optional settings (environment variables)

- `DRIVE_FOLDER_ID` — upload into a specific Drive folder instead of
  "My Drive" root. Get the ID from the folder's URL
  (`drive.google.com/drive/folders/<THIS_PART>`).
- `LINKEDIN_COOKIE` — your own `li_at` session cookie value, only needed
  if you want to save a video from a post that requires being logged in
  to view (e.g. visible only to your connections). Never share this
  cookie with anyone else; it's equivalent to your login session.

## How it works

1. `extractor.py` fetches the LinkedIn post page and looks for the
   direct video CDN URL (LinkedIn embeds it as an `.mp4` or, for
   adaptive streams, an `.m3u8` URL under `dms.licdn.com`).
2. `app.py` downloads that video to a temp file.
3. `drive_uploader.py` uploads it to your Google Drive via the Drive
   API and returns a shareable link.

## Limitations

- Only works for posts where LinkedIn actually embeds a video (not
  external links, articles, or LinkedIn Learning courses).
- Private/connections-only posts need `LINKEDIN_COOKIE` set to your own
  session cookie.
- If LinkedIn changes how it embeds video URLs, `extractor.py` may need
  updating — the regexes are inherently fragile since there's no
  official API for this.
