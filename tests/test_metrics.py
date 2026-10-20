"""Findings checked against values worked out by hand from the raw inputs."""

import json
from typing import Any

import pytest

from budget_compare import OUTPUT_DIR
from budget_compare.data import load_raw
from budget_compare.metrics import compute_findings, _round

approx = lambda x: pytest.approx(x, abs=0.05)  # noqa: E731 — one decimal place tolerance


@pytest.fixture(scope="module")
def f() -> dict[str, Any]:
    """Findings computed from the raw dataset."""
    return compute_findings(load_raw())


def test_monthly_wages(f: dict[str, Any]) -> None:
    """RM 2,000 / 4.0805 = $490.14; RM 2,000 / 1.35 = Int$1,481.48; THB 12,000 / 9.97 = Int$1,203.61."""
    assert f["wages"]["MYS_2027"]["monthly_usd"] == approx(490.14)
    assert f["wages"]["MYS_2027"]["monthly_ppp"] == approx(1481.48)
    assert f["wages"]["MYS_2026"]["monthly_ppp"] == approx(1259.26)
    assert f["wages"]["THA_CAP"]["monthly_usd"] == approx(358.74)
    assert f["wages"]["THA_CAP"]["monthly_ppp"] == approx(1203.61)
    assert f["wages"]["THA_FLOOR"]["monthly_ppp"] == approx(1014.04)


def test_wage_gaps(f: dict[str, Any]) -> None:
    """Hike, nominal lead and real (PPP) lead."""
    g = f["wage_gaps"]
    assert g["my_wage_hike_pct"] == approx(17.65)            # 2000/1700 - 1
    assert g["my_usd_lead_vs_th_cap_pct"] == approx(36.63)   # 490.14/358.74 - 1
    assert g["my_ppp_lead_vs_th_cap_pct"] == approx(23.09)   # 1481.48/1203.61 - 1
    assert g["my_ppp_lead_vs_th_floor_pct"] == approx(46.10) # 1481.48/1014.04 - 1


def test_ppp_narrows_the_gap(f: dict[str, Any]) -> None:
    """Thailand's lower prices shrink Malaysia's lead once wages are price-adjusted."""
    g = f["wage_gaps"]
    assert g["my_ppp_lead_vs_th_cap_pct"] < g["my_usd_lead_vs_th_cap_pct"]
    assert g["my_ppp_lead_vs_th_floor_pct"] < g["my_usd_lead_vs_th_floor_pct"]


def test_casual_worker_sensitivity(f: dict[str, Any]) -> None:
    """26 paid days: THB 8,762 and THB 10,400; Malaysia's lead widens to +42.0% / +68.6%."""
    s = f["casual_worker_sensitivity"]
    assert s["th_floor_monthly_thb_26d"] == 8762
    assert s["th_cap_monthly_thb_26d"] == 10400
    assert s["monthly_pay_cut_pct"] == approx(13.33)
    assert s["my_ppp_lead_vs_th_cap_pct"] == approx(42.02)
    assert s["my_ppp_lead_vs_th_floor_pct"] == approx(68.57)


def test_wage_vs_income(f: dict[str, Any]) -> None:
    """Annual minimum wage as % of GDP per capita, and the income gap between countries."""
    w = f["wages"]
    assert w["MYS_2026"]["annual_wage_pct_of_gdp_per_capita"] == approx(33.13)
    assert w["MYS_2027"]["annual_wage_pct_of_gdp_per_capita"] == approx(38.98)
    assert w["THA_FLOOR"]["annual_wage_pct_of_gdp_per_capita"] == approx(43.33)
    assert w["THA_CAP"]["annual_wage_pct_of_gdp_per_capita"] == approx(51.43)
    p = f["prices_and_income"]
    assert p["my_to_th_gdp_per_capita_ratio"] == approx(1.80)
    assert p["th_gdp_per_capita_lower_pct"] == approx(44.53)


def test_ranking_flips(f: dict[str, Any]) -> None:
    """Malaysia pays the most in real terms, yet its wage is the lightest burden relative to income."""
    w = f["wages"]
    by_ppp = sorted(w, key=lambda k: w[k]["monthly_ppp"])
    by_burden = sorted(w, key=lambda k: w[k]["annual_wage_pct_of_gdp_per_capita"])
    assert by_ppp[-1] == "MYS_2027"
    assert by_burden[:2] == ["MYS_2026", "MYS_2027"]


def test_budget_structure(f: dict[str, Any]) -> None:
    """Spending blocks match the headline RM and THB figures."""
    my, th = f["budget"]["malaysia"], f["budget"]["thailand"]
    assert my["day_to_day_pct"] == approx(81.95)
    assert my["day_to_day_pct"] / 100 * 459.8 == pytest.approx(376.8, abs=0.1)  # RM 376.8B opex
    assert my["development_local_bn"] == pytest.approx(83.0, abs=0.1)          # RM 83.0B devex
    assert my["subsidies_and_welfare_local_bn"] == pytest.approx(80.0, abs=0.1) # "RM 80B-plus"
    assert th["day_to_day_pct"] == approx(73.55)
    assert th["development_pct"] == approx(20.83)
    assert th["debt_principal_pct"] == approx(5.61)
    assert th["development_pct"] > my["development_pct"]


def test_off_budget_top_ups(f: dict[str, Any]) -> None:
    """RM 50.2B / RM 459.8B = 10.92%; THB 400B / THB 3,788B = 10.56%."""
    my, th = f["budget"]["malaysia"], f["budget"]["thailand"]
    assert my["off_budget_pct_of_budget"] == approx(10.92)
    assert my["all_in_local_bn"] == pytest.approx(510.0)
    assert th["off_budget_pct_of_budget"] == approx(10.56)


def test_budgets_are_same_size(f: dict[str, Any]) -> None:
    """$112.68B vs $113.24B: less than 0.5% apart."""
    assert 0 < f["budget_size_gap_pct"] < 0.5


def test_findings_json_is_current(f: dict[str, Any]) -> None:
    """outputs/findings.json must equal a fresh computation (run `make run` if this fails)."""
    path = OUTPUT_DIR / "findings.json"
    assert path.exists(), "Run `make run` first"
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(json.dumps(_round(f)))
