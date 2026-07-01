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

## 1. Install dependencies

```bash
cd linkedin-to-drive
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Optional: install [ffmpeg](https://ffmpeg.org/download.html) and make
sure it's on your PATH. Only needed for the rare post whose video is
served as an adaptive `.m3u8` stream instead of a plain `.mp4`.

## 2. Create a Google OAuth client (one-time)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/),
   create a project (or reuse one).
2. Enable the **Google Drive API** for that project (APIs & Services →
   Enable APIs and Services → search "Google Drive API").
3. Go to APIs & Services → Credentials → Create Credentials → OAuth
   client ID.
   - Application type: **Desktop app**.
4. Download the resulting JSON and save it as
   `linkedin-to-drive/credentials.json`.

The app only requests the `drive.file` scope, so it can only see/manage
files it creates itself — not your whole Drive.

## 3. Run it

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser, paste a LinkedIn post link,
and click **Download & upload to Drive**. The first time you upload,
a browser tab will open asking you to sign in to Google and approve
access — after that, a `token.json` is cached locally so you won't be
asked again.

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
