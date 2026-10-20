"""README numbers must agree with the computed findings, and debunked claims must stay out."""

from typing import Any

import pytest

from budget_compare import PROJECT_ROOT
from budget_compare.charts import pct1
from budget_compare.data import load_raw
from budget_compare.metrics import compute_findings

README = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def f() -> dict[str, Any]:
    """Findings computed from the raw dataset."""
    return compute_findings(load_raw())


def expected_strings(f: dict[str, Any]) -> list[str]:
    """Every headline figure, formatted the way the README quotes it."""
    w, g, s = f["wages"], f["wage_gaps"], f["casual_worker_sensitivity"]
    p, my, th = f["prices_and_income"], f["budget"]["malaysia"], f["budget"]["thailand"]
    return [
        f"Int$ {w['MYS_2027']['monthly_ppp']:,.0f}",
        f"Int$ {w['THA_CAP']['monthly_ppp']:,.0f}",
        f"Int$ {w['THA_FLOOR']['monthly_ppp']:,.0f}",
        f"${w['MYS_2027']['monthly_usd']:,.0f}",
        f"${w['THA_CAP']['monthly_usd']:,.0f}",
        f"${w['THA_FLOOR']['monthly_usd']:,.0f}",
        f"+{pct1(g['my_ppp_lead_vs_th_cap_pct'])}",
        f"+{pct1(g['my_ppp_lead_vs_th_floor_pct'])}",
        f"+{pct1(g['my_usd_lead_vs_th_cap_pct'])}",
        f"+{g['my_wage_hike_pct']:.2f}%",
        f"+{pct1(s['my_ppp_lead_vs_th_cap_pct'])}",
        f"+{pct1(s['my_ppp_lead_vs_th_floor_pct'])}",
        f"THB {s['th_floor_monthly_thb_26d']:,}–{s['th_cap_monthly_thb_26d']:,}",
        pct1(s["monthly_pay_cut_pct"]),
        *(pct1(w[k]["annual_wage_pct_of_gdp_per_capita"]) for k in w),
        f"${p['my_gdp_per_capita_usd']:,.0f}",
        f"${p['th_gdp_per_capita_usd']:,.0f}",
        f"{p['my_to_th_gdp_per_capita_ratio']:.1f}×",
        pct1(my["day_to_day_pct"]),
        pct1(my["development_pct"]),
        pct1(my["subsidies_and_welfare_pct"]),
        f"RM {my['development_local_bn']:.1f}B",
        f"RM {my['off_budget_local_bn']:.1f}B",
        f"+{pct1(my['off_budget_pct_of_budget'])}",
        f"RM {my['all_in_local_bn']:.0f}B",
        pct1(th["day_to_day_pct"]),
        pct1(th["development_pct"]),
        pct1(th["debt_and_reserves_pct"]),
        f"THB {th['development_local_bn']:.0f}B",
        f"THB {th['off_budget_local_bn']:.0f}B",
        f"+{pct1(th['off_budget_pct_of_budget'])}",
        f"US${my['total_usd_bn']:.1f}B",
        f"US${th['total_usd_bn']:.1f}B",
    ]


def test_readme_quotes_every_headline_number(f: dict[str, Any]) -> None:
    """Each computed headline figure appears verbatim in the README."""
    missing = [s for s in expected_strings(f) if s not in README]
    assert not missing, f"README is missing or misquotes: {missing}"


@pytest.mark.parametrize("claim", ["40% threshold", "caution threshold", "Kaitz", "13 million"])
def test_readme_avoids_debunked_claims(claim: str) -> None:
    """Claims from the earlier draft that could not be verified must not reappear."""
    assert claim.lower() not in README.lower()


def test_readme_links_existing_files() -> None:
    """Images and files referenced from the README exist in the repo."""
    import re
    for target in re.findall(r"\]\(((?:outputs|data)/[^)]+)\)", README):
        assert (PROJECT_ROOT / target).exists(), target
