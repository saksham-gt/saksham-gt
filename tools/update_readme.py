#!/usr/bin/env python3
"""Refresh the auto-updating sections of README.md.

Sections are delimited by HTML comments, e.g.
    <!-- blog:start --> ... <!-- blog:end -->

- blog:    latest posts from the RSS feed (no credentials needed)
- spotify: top tracks of the last ~4 weeks, drawn as assets/on-repeat-*.svg
           with a link list underneath (needs SPOTIFY_CLIENT_ID,
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
from xml.sax.saxutils import escape

from gen_header import FONT, THEMES

README = Path(__file__).resolve().parent.parent / "README.md"
ASSETS = README.parent / "assets"
PAD_X = 24
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
    return render_tracks(tracks)


def clip(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def cover_data_uri(track):
    """Smallest album cover as a data URI (an SVG shown as an image cannot load URLs)."""
    try:
        url = track["album"]["images"][-1]["url"]
        return "data:image/jpeg;base64," + base64.b64encode(fetch(url)).decode()
    except Exception as error:
        print(f"spotify: no cover for {track.get('name')!r}: {error}", file=sys.stderr)
        return None


def tracks_card(tracks, covers, colors):
    row_h, top, size = 54, 56, 40
    height = top + len(tracks) * row_h + 8
    bars = "".join(
        f'<rect x="{PAD_X + i * 7}" y="20" width="4" height="16" rx="2" fill="{colors["accent"]}">'
        f'<animate attributeName="height" values="{a};{b};{a}" dur="{dur}s" repeatCount="indefinite"/>'
        f'<animate attributeName="y" values="{36 - a};{36 - b};{36 - a}" dur="{dur}s" repeatCount="indefinite"/></rect>'
        for i, (a, b, dur) in enumerate([(6, 16, 0.9), (16, 5, 1.1), (9, 16, 0.7), (14, 4, 1.3)])
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 {height}" width="600" height="{height}" '
        f'role="img" aria-label="{escape("On repeat: " + "; ".join(t["name"] for t in tracks), {chr(34): "&quot;"})}">',
        f'<rect x="0.5" y="0.5" width="599" height="{height - 1}" rx="10" fill="{colors["bg"]}" '
        f'stroke="{colors["border"]}"/>',
        f'<g font-family="{FONT}">',
        bars,
        f'<text x="{PAD_X + 38}" y="34" font-size="16" font-weight="700" fill="{colors["text"]}">on repeat</text>',
        f'<text x="{600 - PAD_X}" y="34" font-size="12" fill="{colors["muted"]}" text-anchor="end">last 4 weeks</text>',
    ]
    for index, (track, cover) in enumerate(zip(tracks, covers)):
        y = top + index * row_h
        parts.append(f'<clipPath id="k{index}"><rect x="{PAD_X}" y="{y}" width="{size}" height="{size}" rx="6"/></clipPath>')
        parts.append(f'<rect x="{PAD_X}" y="{y}" width="{size}" height="{size}" rx="6" fill="{colors["border"]}"/>')
        if cover:
            parts.append(
                f'<image href="{cover}" x="{PAD_X}" y="{y}" width="{size}" height="{size}" '
                f'preserveAspectRatio="xMidYMid slice" clip-path="url(#k{index})"/>'
            )
        artists = ", ".join(artist["name"] for artist in track["artists"])
        parts.append(
            f'<text x="{PAD_X + size + 14}" y="{y + 17}" font-size="15" font-weight="700" fill="{colors["text"]}">'
            f'{escape(clip(track["name"], 52))}</text>'
            f'<text x="{PAD_X + size + 14}" y="{y + 35}" font-size="12" fill="{colors["muted"]}">'
            f"{escape(clip(artists, 64))}</text>"
        )
    parts += ["</g>", "</svg>"]
    return "\n".join(parts) + "\n"


def render_tracks(tracks):
    """Write the on-repeat cards and return the README block that shows them."""
    covers = [cover_data_uri(track) for track in tracks]
    ASSETS.mkdir(exist_ok=True)
    for name, colors in THEMES.items():
        (ASSETS / f"on-repeat-{name}.svg").write_text(tracks_card(tracks, covers, colors), encoding="utf-8")
    links = []
    for number, track in enumerate(tracks, 1):
        artists = ", ".join(md(artist["name"]) for artist in track["artists"])
        links.append(f"{number}. [{md(track['name'])}]({track['external_urls']['spotify']}) by {artists}")
    alt = "Top tracks of the last four weeks: " + "; ".join(clip(track["name"], 40) for track in tracks)
    return (
        "<picture>\n"
        '  <source media="(prefers-color-scheme: dark)" srcset="assets/on-repeat-dark.svg">\n'
        f'  <img src="assets/on-repeat-light.svg" width="600" alt="{escape(alt, {chr(34): "&quot;"})}">\n'
        "</picture>\n\n"
        "<details>\n<summary>Listen on Spotify</summary>\n\n" + "\n".join(links) + "\n\n</details>"
    )


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
