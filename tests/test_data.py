"""Integrity checks: the raw CSV is untouched and its derived columns follow from its inputs."""

import pandas as pd
import pytest

from budget_compare.data import BUDGET_SHARE_COLUMNS, EXPECTED_SHA256, RECORD_IDS, file_sha256, load_raw
from budget_compare import RAW_CSV


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    """Validated raw dataset."""
    return load_raw()


def test_raw_file_checksum_is_pinned() -> None:
    """The raw CSV must be byte-identical to the original source."""
    assert file_sha256(RAW_CSV) == EXPECTED_SHA256


def test_records_and_countries(df: pd.DataFrame) -> None:
    """Exactly two Malaysian and two Thai records, in a fixed order."""
    assert list(df.index) == RECORD_IDS
    assert list(df["country"]) == ["Malaysia", "Malaysia", "Thailand", "Thailand"]
    assert list(df["currency_code"]) == ["MYR", "MYR", "THB", "THB"]


def test_nominal_wage_matches_exchange_rate(df: pd.DataFrame) -> None:
    """nominal_wage_usd = monthly wage / market exchange rate."""
    expected = df["monthly_wage_lcu"] / df["exchange_rate_lcu_per_usd"]
    assert (expected - df["nominal_wage_usd"]).abs().max() < 0.01


def test_ppp_wage_matches_ppp_rate(df: pd.DataFrame) -> None:
    """ppp_wage_int_dlr = monthly wage / PPP conversion rate."""
    expected = df["monthly_wage_lcu"] / df["ppp_rate_lcu_per_int_dlr"]
    assert (expected - df["ppp_wage_int_dlr"]).abs().max() < 0.01


def test_price_level_index(df: pd.DataFrame) -> None:
    """Price level index = PPP rate / exchange rate × 100."""
    expected = df["ppp_rate_lcu_per_int_dlr"] / df["exchange_rate_lcu_per_usd"] * 100
    assert (expected - df["price_level_index"]).abs().max() < 0.01


def test_wage_to_gdp_ratio(df: pd.DataFrame) -> None:
    """annual_wage_to_gdp_pct = 12 × monthly USD wage / GDP per capita × 100."""
    expected = 12 * df["monthly_wage_lcu"] / df["exchange_rate_lcu_per_usd"] / df["gdp_per_capita_usd"] * 100
    assert (expected - df["annual_wage_to_gdp_pct"]).abs().max() < 0.01


def test_thai_monthly_wage_is_30_days_of_daily_rate(df: pd.DataFrame) -> None:
    """Thai monthly figures are 30 × the THB 337 and THB 400 daily rates."""
    assert df.loc["THA_FLOOR", "monthly_wage_lcu"] == 30 * 337
    assert df.loc["THA_CAP", "monthly_wage_lcu"] == 30 * 400


def test_budget_shares_sum_to_100(df: pd.DataFrame) -> None:
    """On-budget shares add to 100% (Thai source rounds to 99.99)."""
    totals = df[BUDGET_SHARE_COLUMNS].sum(axis=1)
    assert ((totals - 100).abs() <= 0.02).all()


def test_budget_totals_match_local_currency_headlines(df: pd.DataFrame) -> None:
    """USD budgets equal RM 459.8B and THB 3,788B at the dataset's exchange rates."""
    my = df.loc["MYS_2027"]
    th = df.loc["THA_CAP"]
    assert my["total_budget_usd_bn"] == pytest.approx(459.8 / my["exchange_rate_lcu_per_usd"], abs=0.01)
    assert th["total_budget_usd_bn"] == pytest.approx(3788.0 / th["exchange_rate_lcu_per_usd"], abs=0.01)


def test_country_level_fields_constant_within_country(df: pd.DataFrame) -> None:
    """Macro and budget fields do not vary between records of the same country."""
    cols = ["exchange_rate_lcu_per_usd", "ppp_rate_lcu_per_int_dlr", "gdp_per_capita_usd", "total_budget_usd_bn",
            *BUDGET_SHARE_COLUMNS, "off_budget_stimulus_pct"]
    assert (df.groupby("country")[cols].nunique() == 1).all().all()
