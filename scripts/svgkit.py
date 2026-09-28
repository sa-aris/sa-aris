"""Shared palette and tiny helpers for the profile's hand-built SVG figures.

Everything here is standard-library only so the GitHub Action needs no
dependencies. SVGs embedded through <img> cannot load web fonts, so the
font stacks below fall back to whatever the viewer's system provides.
"""

from __future__ import annotations

from html import escape

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
SERIF = "Charter, 'Bitstream Charter', 'Sitka Text', Cambria, Georgia, 'Times New Roman', serif"

PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "panel": "#0b0f16",
        "panel2": "#111823",
        "grid": "#18202c",
        "border": "#263041",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "faint": "#3a4454",
        "blue": "#58a6ff",
        "cyan": "#39c5cf",
        "violet": "#a371f7",
        "pink": "#f778ba",
        "amber": "#e3b341",
        "green": "#56d364",
        "red": "#ff7b72",
    },
    "light": {
        "bg": "#ffffff",
        "panel": "#f6f8fa",
        "panel2": "#ffffff",
        "grid": "#e4e9ef",
        "border": "#d0d7de",
        "text": "#1f2328",
        "muted": "#59636e",
        "faint": "#c4ccd6",
        "blue": "#0969da",
        "cyan": "#1b7c83",
        "violet": "#8250df",
        "pink": "#bf3989",
        "amber": "#9a6700",
        "green": "#1a7f37",
        "red": "#cf222e",
    },
}

THEMES = tuple(PALETTES)


def esc(text: object) -> str:
    return escape(str(text), quote=True)


def fmt(value: float) -> str:
    """Compact coordinate formatting keeps the files small."""
    out = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if out in ("-0", "") else out


def points_to_path(points, closed: bool = False) -> str:
    head, *rest = points
    d = f"M{fmt(head[0])} {fmt(head[1])}" + "".join(f"L{fmt(x)} {fmt(y)}" for x, y in rest)
    return d + ("Z" if closed else "")


def document(width: int, height: int, body: str, title: str, desc: str = "", style: str = "") -> str:
    """Wrap figure markup in an accessible, self-contained SVG document."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        + (f"<style>{style}</style>" if style else "")
        + body
        + "</svg>\n"
    )


def text_width(text: str, size: float, mono: bool = False) -> float:
    """Rough advance-width estimate used for wrapping and label layout."""
    if mono:
        return len(text) * size * 0.6
    narrow = sum(ch in "iljtfr.,:;'!| " for ch in text)
    wide = sum(ch in "mwMW@%" for ch in text)
    caps = sum(ch.isupper() for ch in text)
    return size * (0.52 * len(text) - 0.22 * narrow + 0.3 * wide + 0.12 * caps)


def wrap(text: str, size: float, max_width: float, max_lines: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if text_width(trial, size) <= max_width:
            line = trial
            continue
        if line:
            lines.append(line)
        line = word
        if len(lines) == max_lines:
            break
    if line and len(lines) < max_lines:
        lines.append(line)
    if len(lines) == max_lines and " ".join(lines) != " ".join(words):
        last = lines[-1]
        while last and text_width(last + "…", size) > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip(" ,;:—-") + "…"
    return lines


class Rng:
    """Deterministic xorshift PRNG so regenerated figures are byte-stable."""

    def __init__(self, seed: int):
        self.state = (seed or 1) & 0xFFFFFFFF

    def random(self) -> float:
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x & 0xFFFFFFFF
        return self.state / 0x100000000

    def uniform(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.random()

    def gauss(self) -> float:
        # Irwin–Hall approximation: plenty for visual noise.
        return sum(self.random() for _ in range(12)) - 6.0
