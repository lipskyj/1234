"""Extracts a direct video URL from a public LinkedIn post page."""
from __future__ import annotations

import os
import re

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_MP4_RE = re.compile(r"https://dms\.licdn\.com/[^\s\"']+?\.mp4[^\s\"']*")
_M3U8_RE = re.compile(r"https://dms\.licdn\.com/[^\s\"']+?\.m3u8[^\s\"']*")
_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]+)"')


class LinkedInExtractionError(Exception):
    """Raised when a video URL can't be found or the page can't be fetched."""


def extract_video(post_url: str) -> tuple[str, str]:
    """Fetch a LinkedIn post page and pull out a direct video URL + a title.

    Returns (video_url, title). Raises LinkedInExtractionError on failure.
    """
    headers = dict(_HEADERS)
    cookie = os.environ.get("LINKEDIN_COOKIE")  # optional li_at session cookie
    if cookie:
        headers["Cookie"] = f"li_at={cookie}"

    try:
        resp = requests.get(post_url, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise LinkedInExtractionError(f"Couldn't reach LinkedIn: {exc}") from exc

    if resp.status_code != 200:
        raise LinkedInExtractionError(
            f"LinkedIn returned status {resp.status_code}. The post may be private, "
            "removed, or require you to be logged in (set the LINKEDIN_COOKIE env "
            "var to your own li_at cookie to access posts visible to you)."
        )

    if "authwall" in resp.url or resp.url.rstrip("/").endswith("/login"):
        raise LinkedInExtractionError(
            "LinkedIn redirected to a login page instead of the post. It's "
            "blocking anonymous requests for this one (common even for posts "
            "that look public). Set the LINKEDIN_COOKIE env var to your own "
            "li_at session cookie and try again."
        )

    html = resp.text

    mp4_matches = sorted(set(_MP4_RE.findall(html)), key=len, reverse=True)
    if mp4_matches:
        video_url = _unescape(mp4_matches[0])
    else:
        m3u8_matches = sorted(set(_M3U8_RE.findall(html)), key=len, reverse=True)
        if not m3u8_matches:
            raise LinkedInExtractionError(
                "Couldn't find a video on that page. Make sure the link points "
                "directly to a LinkedIn post containing a video and that it's "
                "publicly viewable (or set LINKEDIN_COOKIE for posts only you can see)."
            )
        video_url = _unescape(m3u8_matches[0])

    title_match = _TITLE_RE.search(html)
    title = title_match.group(1) if title_match else "linkedin_video"

    return video_url, title


def _unescape(url: str) -> str:
    url = url.replace("\\u0026", "&").replace("&amp;", "&")
    return url.rstrip("\\")
