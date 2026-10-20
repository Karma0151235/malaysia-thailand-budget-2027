"""Chart exports exist in every variant, are print-quality, and carry the right numbers."""

from pathlib import Path

import pytest
from PIL import Image

from budget_compare import OUTPUT_DIR
from budget_compare.charts import pct1

CHARTS = ["1_real_wage_ppp", "2_wage_vs_income", "3_budget_split"]
CHART_DIR = OUTPUT_DIR / "charts"


@pytest.mark.parametrize("name", CHARTS)
def test_all_variants_exist(name: str) -> None:
    """White PNG, transparent PNG and SVG are written for every chart."""
    for path in (CHART_DIR / "png_white" / f"{name}.png",
                 CHART_DIR / "png_transparent" / f"{name}.png",
                 CHART_DIR / "svg" / f"{name}.svg"):
        assert path.exists() and path.stat().st_size > 0, f"missing {path}"


@pytest.mark.parametrize("name", CHARTS)
def test_png_resolution(name: str) -> None:
    """PNGs are 300 DPI and at least 2,400 px wide for sharp poster printing."""
    with Image.open(CHART_DIR / "png_white" / f"{name}.png") as im:
        dpi = im.info.get("dpi", (0, 0))
        assert round(dpi[0]) >= 300
        assert im.width >= 2400


@pytest.mark.parametrize("name", CHARTS)
def test_white_vs_transparent_background(name: str) -> None:
    """White variant has an opaque white corner; transparent variant has a see-through corner."""
    with Image.open(CHART_DIR / "png_white" / f"{name}.png") as im:
        assert im.convert("RGBA").getpixel((2, 2)) == (255, 255, 255, 255)
    with Image.open(CHART_DIR / "png_transparent" / f"{name}.png") as im:
        assert im.mode == "RGBA"
        assert im.getpixel((2, 2))[3] == 0


def test_pct1_rounds_halves_up() -> None:
    """Labels round 81.95 to 82.0% and 18.05 to 18.1%, matching how the source would be read."""
    assert pct1(81.95) == "82.0%"
    assert pct1(18.05) == "18.1%"
    assert pct1(73.55) == "73.6%"
    assert pct1(23.09) == "23.1%"


def test_chart_labels_match_findings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Text drawn on each chart contains the headline values from compute_findings()."""
    import matplotlib.pyplot as plt
    from budget_compare import charts
    from budget_compare.data import load_raw
    from budget_compare.metrics import compute_findings

    f = compute_findings(load_raw())
    captured: dict[str, str] = {}

    def fake_save(fig: plt.Figure, out_dir: Path, name: str) -> list[Path]:
        captured[name] = " ".join(t.get_text() for ax in fig.axes for t in ax.texts)
        plt.close(fig)
        return []

    monkeypatch.setattr(charts, "save_variants", fake_save)
    charts.draw_all(f, tmp_path)

    assert "$1,481" in captured["1_real_wage_ppp"]
    assert "$1,204" in captured["1_real_wage_ppp"]
    assert "+23.1%" in captured["1_real_wage_ppp"]
    for v in ("39.0%", "33.1%", "51.4%", "43.3%"):
        assert v in captured["2_wage_vs_income"]
    for v in ("82.0%", "18.1%", "73.6%", "20.8%", "5.6%", "+10.9%", "+10.6%", "RM 50.2B", "THB 400B"):
        assert v in captured["3_budget_split"]
