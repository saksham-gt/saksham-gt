#!/usr/bin/env python3
"""Refresh the auto-updating sections of README.md.

Sections are delimited by HTML comments, e.g.
    <!-- blog:start --> ... <!-- blog:end -->

- blog:    latest posts from the RSS feed (no credentials needed)
- spotify: top tracks of the last ~4 weeks (needs SPOTIFY_CLIENT_ID,
           SPOTIFY_CLIENT_SECRET and SPOTIFY_REFRESH_TOKEN; skipped if unset)

Standard library only, so the GitHub Action needs no install step.
"""
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
FEED_URL = "https://blogs.sakshamgt.com/rss.xml"
POST_COUNT = 3
TRACK_COUNT = 5
TIMEOUT = 20


def fetch(url, data=None, headers=None):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": "profile-readme", **(headers or {})})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def md(text):
    """Escape the characters that would break a Markdown link label."""
    return re.sub(r"([\[\]|])", r"\\\1", " ".join(text.split()))


def blog_section():
    feed = fetch(FEED_URL)
    if b"<!DOCTYPE" in feed or b"<!ENTITY" in feed:  # a plain RSS feed never needs these
        raise RuntimeError("feed contains a DTD; refusing to parse")
    items = ET.fromstring(feed).findall("./channel/item")[:POST_COUNT]
    if not items:
        raise RuntimeError("feed has no items")
    lines = []
    for item in items:
        date = parsedate_to_datetime(item.findtext("pubDate")).strftime("%b %Y")
        lines.append(f"- [{md(item.findtext('title'))}]({item.findtext('link')}) <sub>{date}</sub>")
    return "\n".join(lines)


def spotify_section():
    env = {key: os.environ.get(key) for key in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN")}
    if not all(env.values()):
        return None
    basic = base64.b64encode(f"{env['SPOTIFY_CLIENT_ID']}:{env['SPOTIFY_CLIENT_SECRET']}".encode()).decode()
    token = json.loads(
        fetch(
            "https://accounts.spotify.com/api/token",
            data=urllib.parse.urlencode(
                {"grant_type": "refresh_token", "refresh_token": env["SPOTIFY_REFRESH_TOKEN"]}
            ).encode(),
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        )
    )["access_token"]
    tracks = json.loads(
        fetch(
            f"https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit={TRACK_COUNT}",
            headers={"Authorization": f"Bearer {token}"},
        )
    )["items"]
    if not tracks:
        raise RuntimeError("Spotify returned no top tracks")
    lines = []
    for number, track in enumerate(tracks, 1):
        artists = ", ".join(md(artist["name"]) for artist in track["artists"])
        lines.append(f"{number}. [{md(track['name'])}]({track['external_urls']['spotify']}) by {artists}")
    return "\n".join(lines)


def replace_block(text, name, body):
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise RuntimeError(f"README has no {name} markers")
    return pattern.sub(lambda match: match.group(1) + body + "\n" + match.group(2), text)


def main():
    text = original = README.read_text(encoding="utf-8")
    failed = False
    for name, build in (("blog", blog_section), ("spotify", spotify_section)):
        try:
            body = build()
            if body is None:
                print(f"{name}: skipped (credentials not set)")
                continue
            text = replace_block(text, name, body)
            print(f"{name}: ok")
        except Exception as error:  # keep the other section updating
            failed = True
            print(f"{name}: FAILED: {error}", file=sys.stderr)
    if text != original:
        README.write_text(text, encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
