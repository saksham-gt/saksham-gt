#!/usr/bin/env python3
"""Generate the open source tiles for the profile README.

Edit PROJECTS below, then run:  python3 tools/gen_cards.py
Writes assets/oss-<slug>-{dark,light}.svg.
"""
from pathlib import Path
from xml.sax.saxutils import escape

from gen_header import FONT, THEMES

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# (slug, title, merged PR count)
PROJECTS = [
    ("collaction", "CollAction", 24),
    ("talawa", "Talawa", 5),
    ("flutter-tflite", "flutter-tflite", 2),
]

WIDTH, HEIGHT = 188, 96

# Heading icons: outlines from Feather (feathericons.com, MIT). One green that
# reads on both light and dark backgrounds, so no per-theme copies are needed.
ICON_COLOR = "#2da44e"
ICONS = {
    "writing": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    "open-source": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>',
    "made": '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 '
    '2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96 12 12.01l8.73-5.05"/><path d="M12 22.08V12"/>',
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "hi": '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 '
    '0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>',
}


def icon(paths):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" '
        f'stroke="{ICON_COLOR}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>\n'
    )


def oss_tile(colors, title, count):
    most = max(project_count for _, _, project_count in PROJECTS)
    label = f"{title}: {count} merged pull requests"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" '
        f'height="{HEIGHT}" role="img" aria-label="{escape(label)}">\n'
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" '
        f'fill="{colors["bg"]}" stroke="{colors["border"]}"/>\n'
        f'<g font-family="{FONT}">\n'
        f'<text x="16" y="28" font-size="14" font-weight="700" fill="{colors["text"]}">{escape(title)}</text>\n'
        f'<text x="16" y="66" font-size="34" font-weight="700" fill="{colors["accent"]}">{count}</text>\n'
        f'<text x="{16 + len(str(count)) * 20.4 + 8:.1f}" y="66" font-size="12" fill="{colors["muted"]}">'
        f"merged PR{'s' if count != 1 else ''}</text>\n"
        f'<rect x="16" y="78" width="156" height="4" rx="2" fill="{colors["border"]}"/>\n'
        f'<rect x="16" y="78" width="{156 * count / most:.1f}" height="4" rx="2" fill="{colors["accent"]}">'
        f'<animate attributeName="width" from="0" to="{156 * count / most:.1f}" dur="1s" fill="freeze"/></rect>\n'
        f"</g>\n</svg>\n"
    )


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, colors in THEMES.items():
        for slug, title, count in PROJECTS:
            (ASSETS / f"oss-{slug}-{name}.svg").write_text(oss_tile(colors, title, count), encoding="utf-8")
    for name, paths in ICONS.items():
        (ASSETS / f"icon-{name}.svg").write_text(icon(paths), encoding="utf-8")
    print(f"wrote {len(PROJECTS)} tiles in {len(THEMES)} themes and {len(ICONS)} icons to assets/")


if __name__ == "__main__":
    main()
