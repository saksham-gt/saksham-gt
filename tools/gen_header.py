#!/usr/bin/env python3
"""Generate the typed-text header SVGs for the profile README.

Edit NAME / LINES below, then run:  python3 tools/gen_header.py
Writes assets/header-dark.svg and assets/header-light.svg.
"""
from pathlib import Path
from xml.sax.saxutils import escape

NAME = "Saksham Gupta"

# Lines that get typed and erased in turn. Keep each under MAX_CHARS.
LINES = [
    "engineer at Fam, previously at Dyte",
    "problem solver, martial artist, Punjabi music fan",
    "open source: CollAction, Talawa, flutter-tflite",
    "writing at blogs.sakshamgt.com",
]

MAX_CHARS = 50
WIDTH, HEIGHT = 600, 156
FONT_SIZE = 18
CHAR_W = 10.8  # 0.6em, enforced with textLength so any monospace font fits
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

TYPE_S, ERASE_S, HOLD_S, GAP_S = 0.055, 0.025, 1.9, 0.45

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", text="#e6edf3", muted="#8b949e", accent="#3fb950"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", muted="#59636e", accent="#1a7f37"),
}

LEFT = 24
TYPED_X = LEFT + 2 * CHAR_W  # after the "> " prompt
TYPED_Y = 128


def timeline():
    """Return (total_seconds, per-line [(time, chars_visible)])."""
    t, tracks = 0.0, []
    for line in LINES:
        n, events = len(line), []
        for i in range(1, n + 1):
            events.append((t, i))
            t += TYPE_S
        t += HOLD_S
        for i in range(n - 1, -1, -1):
            events.append((t, i))
            t += ERASE_S
        t += GAP_S
        tracks.append(events)
    return t, tracks


def animate(attr, events, total, scale, offset=0.0, rest=0.0):
    """Discrete SMIL animation stepping through (time, chars) events."""
    pts = [(0.0, rest)] + [(time, offset + chars * scale) for time, chars in events]
    if pts[1][0] == 0.0:
        pts = pts[1:]
    values = ";".join(f"{v:.1f}" for _, v in pts)
    times = ";".join(f"{time / total:.5f}" for time, _ in pts)
    return (
        f'<animate attributeName="{attr}" calcMode="discrete" dur="{total:.2f}s" '
        f'repeatCount="indefinite" values="{values}" keyTimes="{times}"/>'
    )


def build(c):
    total, tracks = timeline()
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}" role="img" '
        f'aria-label="{escape(NAME)}: {escape("; ".join(LINES))}">',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
        f'<g fill="{c["border"]}"><circle cx="22" cy="20" r="5"/>'
        f'<circle cx="40" cy="20" r="5"/><circle cx="58" cy="20" r="5"/></g>',
        f'<g font-family="{FONT}" font-size="{FONT_SIZE}">',
        f'<text x="{LEFT}" y="60" fill="{c["muted"]}">'
        f'<tspan fill="{c["accent"]}">$</tspan> whoami</text>',
        f'<text x="{LEFT}" y="94" fill="{c["text"]}" font-size="24" font-weight="700">'
        f"{escape(NAME)}</text>",
        f'<text x="{LEFT}" y="{TYPED_Y}" fill="{c["accent"]}">&gt;</text>',
    ]
    cursor_events = []
    for i, (line, events) in enumerate(zip(LINES, tracks)):
        cursor_events += events
        parts.append(
            f'<clipPath id="c{i}"><rect x="{TYPED_X:.1f}" y="{TYPED_Y - 20}" width="0" height="28">'
            f'{animate("width", events + [(events[-1][0], 0)], total, CHAR_W)}</rect></clipPath>'
        )
        parts.append(
            f'<text x="{TYPED_X:.1f}" y="{TYPED_Y}" fill="{c["text"]}" clip-path="url(#c{i})" '
            f'textLength="{len(line) * CHAR_W:.1f}" lengthAdjust="spacing" '
            f'xml:space="preserve">{escape(line)}</text>'
        )
    parts.append(
        f'<rect x="{TYPED_X:.1f}" y="{TYPED_Y - 16}" width="9" height="20" fill="{c["accent"]}">'
        f'{animate("x", cursor_events, total, CHAR_W, offset=TYPED_X, rest=TYPED_X)}'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
        f'dur="1s" repeatCount="indefinite"/></rect>'
    )
    parts += ["</g>", "</svg>"]
    return "\n".join(parts) + "\n"


def main():
    too_long = [line for line in LINES if len(line) > MAX_CHARS]
    if too_long:
        raise SystemExit(f"Lines over {MAX_CHARS} chars: {too_long}")
    out = Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for name, colors in THEMES.items():
        path = out / f"header-{name}.svg"
        path.write_text(build(colors), encoding="utf-8")
        print(f"wrote {path.relative_to(out.parent)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
