"""Every number used in the charts, README and poster is computed here."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

# Headline local-currency figures from the budget announcements (see README references).
# They are not in the CSV; tests check the CSV's USD totals agree with them.
MY_BUDGET_RM_BN = 459.8
MY_OPEX_RM_BN = 376.8
MY_DEVEX_RM_BN = 83.0
MY_OFF_BUDGET_INVESTMENT_RM_BN = 50.2   # GLICs + statutory bodies/MOF Inc + public-private
TH_BUDGET_THB_BN = 3788.0
TH_EMERGENCY_LOAN_THB_BN = 400.0        # Emergency borrowing decree, May 2026 (outside the Budget Act)

TH_DAILY_RATES_THB = {"THA_FLOOR": 337, "THA_CAP": 400}
STATUTORY_DAYS = 30
CASUAL_DAYS = 26


def pct_more(a: float, b: float) -> float:
    """How many percent larger a is than b."""
    return (a / b - 1) * 100


def wage_table(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Monthly minimum wage in local currency, US dollars, PPP dollars, and as a share of GDP per capita."""
    out = {}
    for rid, row in df.iterrows():
        usd = row["monthly_wage_lcu"] / row["exchange_rate_lcu_per_usd"]
        out[rid] = {
            "label": row["regime_label"],
            "monthly_local": row["monthly_wage_lcu"],
            "monthly_usd": usd,
            "monthly_ppp": row["monthly_wage_lcu"] / row["ppp_rate_lcu_per_int_dlr"],
            "annual_wage_pct_of_gdp_per_capita": 12 * usd / row["gdp_per_capita_usd"] * 100,
        }
    return out


def casual_worker_sensitivity(df: pd.DataFrame) -> dict[str, float]:
    """Recompute Malaysia's real-wage lead if Thai workers are paid for 26 days instead of 30."""
    my_ppp = df.loc["MYS_2027", "monthly_wage_lcu"] / df.loc["MYS_2027", "ppp_rate_lcu_per_int_dlr"]
    th_ppp_rate = df.loc["THA_CAP", "ppp_rate_lcu_per_int_dlr"]
    floor_26 = TH_DAILY_RATES_THB["THA_FLOOR"] * CASUAL_DAYS
    cap_26 = TH_DAILY_RATES_THB["THA_CAP"] * CASUAL_DAYS
    return {
        "th_floor_monthly_thb_26d": floor_26,
        "th_cap_monthly_thb_26d": cap_26,
        "monthly_pay_cut_pct": (1 - CASUAL_DAYS / STATUTORY_DAYS) * 100,
        "my_ppp_lead_vs_th_cap_pct": pct_more(my_ppp, cap_26 / th_ppp_rate),
        "my_ppp_lead_vs_th_floor_pct": pct_more(my_ppp, floor_26 / th_ppp_rate),
    }


def budget_structure(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """On-budget spending blocks and the size of each country's off-budget top-up, as % of the budget."""
    my = df.loc["MYS_2027"]
    th = df.loc["THA_CAP"]
    return {
        "malaysia": {
            "total_local_bn": MY_BUDGET_RM_BN,
            "total_usd_bn": my["total_budget_usd_bn"],
            "day_to_day_pct": my["core_operating_pct"] + my["social_subsidies_pct"],
            "subsidies_and_welfare_pct": my["social_subsidies_pct"],
            "subsidies_and_welfare_local_bn": my["social_subsidies_pct"] / 100 * MY_BUDGET_RM_BN,
            "development_pct": my["capital_dev_pct"],
            "development_local_bn": my["capital_dev_pct"] / 100 * MY_BUDGET_RM_BN,
            "debt_principal_pct": my["principal_treasury_pct"],
            "off_budget_local_bn": MY_OFF_BUDGET_INVESTMENT_RM_BN,
            "off_budget_pct_of_budget": MY_OFF_BUDGET_INVESTMENT_RM_BN / MY_BUDGET_RM_BN * 100,
            "all_in_local_bn": MY_BUDGET_RM_BN + MY_OFF_BUDGET_INVESTMENT_RM_BN,
        },
        "thailand": {
            "total_local_bn": TH_BUDGET_THB_BN,
            "total_usd_bn": th["total_budget_usd_bn"],
            "day_to_day_pct": th["core_operating_pct"] + th["social_subsidies_pct"],
            "development_pct": th["capital_dev_pct"],
            "development_local_bn": th["capital_dev_pct"] / 100 * TH_BUDGET_THB_BN,
            "debt_principal_pct": th["principal_treasury_pct"],
            "off_budget_local_bn": TH_EMERGENCY_LOAN_THB_BN,
            "off_budget_pct_of_budget": TH_EMERGENCY_LOAN_THB_BN / TH_BUDGET_THB_BN * 100,
        },
    }


def compute_findings(df: pd.DataFrame) -> dict[str, Any]:
    """Assemble every headline finding into one nested dictionary."""
    w = wage_table(df)
    my26, my27, floor, cap = (w[k] for k in ("MYS_2026", "MYS_2027", "THA_FLOOR", "THA_CAP"))
    budget = budget_structure(df)
    my_gdp = df.loc["MYS_2027", "gdp_per_capita_usd"]
    th_gdp = df.loc["THA_CAP", "gdp_per_capita_usd"]

    return {
        "wages": w,
        "wage_gaps": {
            "my_wage_hike_pct": pct_more(my27["monthly_local"], my26["monthly_local"]),
            "my_usd_lead_vs_th_cap_pct": pct_more(my27["monthly_usd"], cap["monthly_usd"]),
            "my_usd_lead_vs_th_floor_pct": pct_more(my27["monthly_usd"], floor["monthly_usd"]),
            "my_ppp_lead_vs_th_cap_pct": pct_more(my27["monthly_ppp"], cap["monthly_ppp"]),
            "my_ppp_lead_vs_th_floor_pct": pct_more(my27["monthly_ppp"], floor["monthly_ppp"]),
        },
        "casual_worker_sensitivity": casual_worker_sensitivity(df),
        "prices_and_income": {
            "my_price_level_index": df.loc["MYS_2027", "price_level_index"],
            "th_price_level_index": df.loc["THA_CAP", "price_level_index"],
            "my_gdp_per_capita_usd": my_gdp,
            "th_gdp_per_capita_usd": th_gdp,
            "my_to_th_gdp_per_capita_ratio": my_gdp / th_gdp,
            "th_gdp_per_capita_lower_pct": (1 - th_gdp / my_gdp) * 100,
        },
        "budget": budget,
        "budget_size_gap_pct": pct_more(budget["thailand"]["total_usd_bn"], budget["malaysia"]["total_usd_bn"]),
    }


def _round(obj: Any, ndigits: int = 2) -> Any:
    """Recursively round floats for stable JSON output."""
    if isinstance(obj, dict):
        return {k: _round(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, float):
        return round(obj, ndigits)
    if hasattr(obj, "item"):  # numpy scalar
        return _round(obj.item(), ndigits)
    return obj


def write_findings(findings: dict[str, Any], path: Path) -> None:
    """Write findings to JSON, rounded to 2 decimal places."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_round(findings), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
