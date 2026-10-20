"""Shared look for poster charts: palette, typography, and multi-format export."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Identity colours stay fixed across every chart: Malaysia = blue, Thailand = orange.
MALAYSIA = "#2a78d6"
MALAYSIA_LIGHT = "#86b6ef"   # Malaysia's previous (2026) wage
THAILAND = "#eb6834"
THAILAND_LIGHT = "#f4a582"   # Thailand's lower (provincial) wage
NEUTRAL = "#b9b8b2"          # day-to-day running costs
NEUTRAL_LIGHT = "#dddcd7"    # debt repayment
INK = "#0b0b0b"
INK_MUTED = "#52514e"

CHART_SIZE = (10, 5.2)  # inches; at 300 DPI → 3000 × 1560 px
DPI = 300

VARIANTS = ("png_white", "png_transparent", "svg")


def apply_theme() -> None:
    """Set global Matplotlib defaults for clean, high-contrast poster graphics."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 15,
        "text.color": INK,
        "axes.edgecolor": INK_MUTED,
        "axes.labelcolor": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "hatch.linewidth": 1.6,
        "svg.fonttype": "path",  # text drawn as outlines so it renders identically in Canva
        "svg.hashsalt": "budget-compare",  # stable element IDs → reproducible SVGs
    })


def strip_axes(ax: plt.Axes) -> None:
    """Remove every spine and x tick: bars carry direct value labels instead."""
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", left=False, pad=10)


def save_variants(fig: plt.Figure, out_dir: Path, name: str) -> list[Path]:
    """Save a figure as white PNG, transparent PNG and SVG; return the written paths."""
    paths = []
    for variant in VARIANTS:
        folder = out_dir / variant
        folder.mkdir(parents=True, exist_ok=True)
        ext = "svg" if variant == "svg" else "png"
        path = folder / f"{name}.{ext}"
        transparent = variant != "png_white"
        fig.savefig(
            path,
            dpi=DPI,
            bbox_inches="tight",
            pad_inches=0.25,
            transparent=transparent,
            facecolor="none" if transparent else "white",
            metadata={"Date": None} if ext == "svg" else None,
        )
        paths.append(path)
    plt.close(fig)
    return paths
