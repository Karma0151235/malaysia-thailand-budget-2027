"""Render the README's Sources section as a poster-ready reference image."""

import re
from pathlib import Path

import matplotlib.pyplot as plt

from budget_compare import PROJECT_ROOT
from budget_compare.style import DPI, INK, INK_MUTED, MALAYSIA, THAILAND

SOURCE_LINE = re.compile(r"^(\d+)\.\s+(.*?):\s+<(\S+)>\s*$")

TITLE_PT = 13
BODY_PT = 9.5
URL_PT = 8.5
URL_CHARS = 78       # wrap width for URLs, in characters
LINE_GAP = 1.45      # line height as a multiple of font size
FIG_WIDTH = 14.0     # inches


def parse_sources(readme: Path = PROJECT_ROOT / "README.md") -> list[tuple[str, list[tuple[str, str, str]]]]:
    """Return [(group heading, [(number, description, url), ...]), ...] from the README's Sources section."""
    text = readme.read_text(encoding="utf-8")
    section = text.split("## Sources", 1)[1].split("\n## ", 1)[0]
    groups: list[tuple[str, list[tuple[str, str, str]]]] = []
    for line in section.splitlines():
        if line.startswith("### "):
            groups.append((line[4:].strip(), []))
        elif m := SOURCE_LINE.match(line.strip()):
            num, desc, url = m.groups()
            groups[-1][1].append((num, desc.replace("*", ""), url))
    return groups


def wrap_url(url: str, width: int = URL_CHARS) -> list[str]:
    """Split a long URL into lines, breaking only after '/' or '-' where possible."""
    lines, current = [], ""
    for piece in re.findall(r"[^/-]*[/-]?", url):
        if current and len(current) + len(piece) > width:
            lines.append(current)
            current = ""
        current += piece
    return lines + [current] if current else lines


def _column_lines(groups: list[tuple[str, list[tuple[str, str, str]]]]) -> list[tuple[str, float, str, str]]:
    """Flatten groups into (text, size, colour, weight) rows for one column."""
    rows: list[tuple[str, float, str, str]] = []
    for heading, items in groups:
        if rows:
            rows.append(("", BODY_PT * 0.6, INK, "normal"))
        colour = MALAYSIA if heading.startswith("Malaysia") else THAILAND if heading.startswith("Thailand") else INK
        rows.append((heading, BODY_PT + 1, colour, "bold"))
        for num, desc, url in items:
            rows.append((f"[{num}] {desc}", BODY_PT, INK, "normal"))
            rows.extend((f"      {part}", URL_PT, INK_MUTED, "normal") for part in wrap_url(url))
    return rows


def draw_references(out_dir: Path) -> list[Path]:
    """Draw all sources in two columns (Malaysia | Thailand + international) and save white and transparent PNGs."""
    groups = parse_sources()
    columns = [_column_lines(groups[:1]), _column_lines(groups[1:])]

    def height_pt(rows: list[tuple[str, float, str, str]]) -> float:
        return sum(size * LINE_GAP for _, size, _, _ in rows)

    title_pt = TITLE_PT * 2.4
    fig_height = (title_pt + max(height_pt(c) for c in columns)) / 72 + 0.3
    fig = plt.figure(figsize=(FIG_WIDTH, fig_height))
    to_y = lambda pt: 1 - pt / 72 / fig_height  # noqa: E731 — points from top → figure fraction

    fig.text(0.01, to_y(TITLE_PT), "References", fontsize=TITLE_PT, fontweight="bold", color=INK, va="center")
    for x, rows in zip((0.01, 0.51), columns):
        y_pt = title_pt
        for text, size, colour, weight in rows:
            y_pt += size * LINE_GAP
            fig.text(x, to_y(y_pt), text, fontsize=size, color=colour, fontweight=weight, va="baseline")

    paths = []
    for name, transparent in (("references.png", False), ("references_transparent.png", True)):
        path = out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.2, transparent=transparent,
                    facecolor="none" if transparent else "white")
        paths.append(path)
    plt.close(fig)
    return paths
