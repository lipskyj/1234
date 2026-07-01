"""Handles Google OAuth2 and uploads a local file to the user's Drive."""
from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# drive.file scope: the app can only see/manage files it creates itself,
# not your whole Drive.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

_BASE_DIR = Path(__file__).resolve().parent
_TOKEN_PATH = _BASE_DIR / "token.json"
_CREDENTIALS_PATH = _BASE_DIR / "credentials.json"


def _get_credentials() -> Credentials:
    creds = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _CREDENTIALS_PATH.exists():
                raise RuntimeError(
                    "Missing credentials.json. Download an OAuth client ID (type "
                    "'Desktop app') from Google Cloud Console and save it as "
                    "linkedin-to-drive/credentials.json. See README.md."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        _TOKEN_PATH.write_text(creds.to_json())

    return creds


def upload_file(local_path: Path, drive_name: str) -> str:
    """Upload local_path to Drive and return a shareable webViewLink."""
    creds = _get_credentials()
    service = build("drive", "v3", credentials=creds)

    metadata = {"name": drive_name}
    folder_id = os.environ.get("DRIVE_FOLDER_ID")
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(local_path), mimetype="video/mp4", resumable=True)
    file = (
        service.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    return file.get("webViewLink") or f"https://drive.google.com/file/d/{file['id']}/view"
