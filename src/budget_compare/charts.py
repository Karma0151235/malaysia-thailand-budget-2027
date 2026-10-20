"""The three poster charts. Every number drawn comes from compute_findings()."""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

from budget_compare.style import (
    CHART_SIZE, INK, INK_MUTED, MALAYSIA, MALAYSIA_LIGHT, NEUTRAL, NEUTRAL_LIGHT,
    THAILAND, THAILAND_LIGHT, save_variants, strip_axes,
)

# Same row order in charts 1 and 2 so readers can see the ranking flip.
ROWS = [
    ("MYS_2027", "Malaysia 2027\nRM 2,000/month", MALAYSIA),
    ("MYS_2026", "Malaysia 2026\nRM 1,700/month", MALAYSIA_LIGHT),
    ("THA_CAP", "Thailand – Bangkok\nTHB 400/day", THAILAND),
    ("THA_FLOOR", "Thailand – lowest\nTHB 337/day", THAILAND_LIGHT),
]


def pct1(v: float) -> str:
    """Format a percentage to one decimal, rounding halves up (81.95 → 82.0, not float-rounded 81.9)."""
    return f"{Decimal(str(round(v, 2))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"


def _caption(ax: plt.Axes, text: str) -> None:
    """Small unit caption in the top-left corner (the poster supplies the real title)."""
    ax.text(0, 1.04, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=13, color=INK_MUTED)


def _hbars(ax: plt.Axes, values: list[float], labels: list[str]) -> None:
    """Draw the four wage rows as horizontal bars with direct value labels."""
    ys = list(range(len(ROWS)))[::-1]
    colors = [c for _, _, c in ROWS]
    ax.barh(ys, values, color=colors, height=0.66, edgecolor="white", linewidth=2)
    for y, v, lab in zip(ys, values, labels):
        ax.text(v + max(values) * 0.015, y, lab, va="center", ha="left", fontsize=17, fontweight="bold", color=INK)
    ax.set_yticks(ys, [name for _, name, _ in ROWS], fontsize=14)
    strip_axes(ax)


def real_wage_chart(f: dict[str, Any], out_dir: Path) -> list[Path]:
    """Chart 1: monthly minimum wage after adjusting for local prices (PPP, international dollars)."""
    w = f["wages"]
    values = [w[rid]["monthly_ppp"] for rid, _, _ in ROWS]
    labels = [f"${v:,.0f}" for v in values]

    fig, ax = plt.subplots(figsize=CHART_SIZE)
    _hbars(ax, values, labels)
    ax.set_xlim(0, max(values) * 1.42)
    _caption(ax, "What a month of minimum-wage pay can buy, in price-adjusted dollars (PPP Int$)")

    lead = f["wage_gaps"]["my_ppp_lead_vs_th_cap_pct"]
    x_tip = max(values) * 1.12
    arrow = FancyArrowPatch((x_tip, 1.0), (x_tip, 2.75), arrowstyle="-|>", mutation_scale=22,
                            color=MALAYSIA, linewidth=2.5, connectionstyle="arc3,rad=0")
    ax.add_patch(arrow)
    ax.text(x_tip + max(values) * 0.025, 1.9, f"+{pct1(lead)}\nmore than\nBangkok",
            va="center", ha="left", fontsize=17, fontweight="bold", color=MALAYSIA, linespacing=1.1)
    return save_variants(fig, out_dir, "1_real_wage_ppp")


def wage_vs_income_chart(f: dict[str, Any], out_dir: Path) -> list[Path]:
    """Chart 2: a full year of minimum wage as a share of GDP per capita (average income per person)."""
    w = f["wages"]
    values = [w[rid]["annual_wage_pct_of_gdp_per_capita"] for rid, _, _ in ROWS]
    labels = [pct1(v) for v in values]

    fig, ax = plt.subplots(figsize=CHART_SIZE)
    _hbars(ax, values, labels)
    ax.set_xlim(0, max(values) * 1.6)
    _caption(ax, "A year of minimum wage, as % of average income per person (GDP per capita)")

    p = f["prices_and_income"]
    ax.text(max(values) * 1.24, 1.5,
            f"Average income\nper person\nMalaysia ${p['my_gdp_per_capita_usd']:,.0f}\n"
            f"Thailand ${p['th_gdp_per_capita_usd']:,.0f}",
            va="center", ha="left", fontsize=13.5, color=INK_MUTED, linespacing=1.35)
    return save_variants(fig, out_dir, "2_wage_vs_income")


def budget_split_chart(f: dict[str, Any], out_dir: Path) -> list[Path]:
    """Chart 3: how each budget is split, plus each country's off-budget top-up beyond 100%."""
    my, th = f["budget"]["malaysia"], f["budget"]["thailand"]
    rows = [
        (1, f"Malaysia\nRM {my['total_local_bn']:,.1f}B", my, MALAYSIA,
         f"+{pct1(my['off_budget_pct_of_budget'])} extra\nRM {my['off_budget_local_bn']:.1f}B off-budget\ninvestment (GLICs, PPPs)"),
        (0, f"Thailand\nTHB {th['total_local_bn']:,.0f}B", th, THAILAND,
         f"+{pct1(th['off_budget_pct_of_budget'])} extra\nTHB {th['off_budget_local_bn']:.0f}B emergency\nloan (living costs, energy)"),
    ]

    fig, ax = plt.subplots(figsize=(CHART_SIZE[0], 4.8))
    h = 0.56
    for y, _, b, color, note in rows:
        segments = [
            (b["day_to_day_pct"], NEUTRAL, INK),
            (b["development_pct"], color, "white"),
            (b["debt_and_reserves_pct"], NEUTRAL_LIGHT, INK),
        ]
        left = 0.0
        for width, fill, txt in segments:
            if width <= 0:
                continue
            ax.barh(y, width, left=left, height=h, color=fill, edgecolor="white", linewidth=2)
            if width > 10:
                ax.text(left + width / 2, y, pct1(width), ha="center", va="center", fontsize=17,
                        fontweight="bold", color=txt)
            left += width
        extra = b["off_budget_pct_of_budget"]
        ax.barh(y, extra, left=100, height=h, color="white", edgecolor=color, hatch="///", linewidth=2)
        ax.text(100 + extra + 1.5, y, note, ha="left", va="center", fontsize=12.5, color=INK, linespacing=1.2)

    # Segment names once, above the top bar, instead of a legend.
    top = 1 + h / 2 + 0.06
    ax.text(my["day_to_day_pct"] / 2, top, "Day-to-day running costs\n(salaries, subsidies, interest…)",
            ha="center", va="bottom", fontsize=12.5, color=INK_MUTED, linespacing=1.15)
    ax.text(my["day_to_day_pct"] + my["development_pct"] / 2, top, "Development\n(building)",
            ha="center", va="bottom", fontsize=12.5, color=INK_MUTED, linespacing=1.15)
    debt_mid = th["day_to_day_pct"] + th["development_pct"] + th["debt_and_reserves_pct"] / 2
    ax.annotate(f"Debt repayment & reserves {pct1(th['debt_and_reserves_pct'])}", xy=(debt_mid, -h / 2), xytext=(debt_mid - 1, -0.62),
                ha="right", va="center", fontsize=12.5, color=INK_MUTED,
                arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=1))

    ax.plot([100, 100], [-0.7, 1 + h / 2], color=INK, linewidth=1.5)
    ax.text(101, -0.62, "100% = official budget", ha="left", va="center", fontsize=12.5, color=INK)
    ax.set_xlim(0, 146)
    ax.set_ylim(-0.75, 1.75)
    ax.set_yticks([r[0] for r in rows], [r[1] for r in rows], fontsize=14)
    strip_axes(ax)
    _caption(ax, f"Share of each national budget (both ≈ US${my['total_usd_bn']:.0f}B)")
    return save_variants(fig, out_dir, "3_budget_split")


def draw_all(f: dict[str, Any], out_dir: Path) -> list[Path]:
    """Render all three charts in poster order."""
    return [
        *real_wage_chart(f, out_dir),
        *wage_vs_income_chart(f, out_dir),
        *budget_split_chart(f, out_dir),
    ]
