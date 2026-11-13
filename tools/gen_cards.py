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
    print(f"wrote {len(PROJECTS)} tiles in {len(THEMES)} themes to assets/")


if __name__ == "__main__":
    main()
