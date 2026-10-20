"""Load and validate the raw Malaysia–Thailand dataset."""

import hashlib
from pathlib import Path

import pandas as pd

from budget_compare import RAW_CSV

# SHA-256 of the original source file. If this changes, the raw data was edited.
EXPECTED_SHA256 = "1ad4ea88cc4a77db34c257c0fe1f58ab0e2710b4bc3b267927c4f29e845ab01d"

RECORD_IDS = ["MYS_2026", "MYS_2027", "THA_FLOOR", "THA_CAP"]

NUMERIC_COLUMNS = [
    "exchange_rate_lcu_per_usd",
    "ppp_rate_lcu_per_int_dlr",
    "price_level_index",
    "gdp_per_capita_usd",
    "monthly_wage_lcu",
    "nominal_wage_usd",
    "ppp_wage_int_dlr",
    "annual_wage_to_gdp_pct",
    "total_budget_usd_bn",
    "core_operating_pct",
    "social_subsidies_pct",
    "capital_dev_pct",
    "principal_treasury_pct",
    "off_budget_stimulus_pct",
]

TEXT_COLUMNS = ["record_id", "country", "regime_label", "currency_code", "source_citation_keys"]

BUDGET_SHARE_COLUMNS = [
    "core_operating_pct",
    "social_subsidies_pct",
    "capital_dev_pct",
    "principal_treasury_pct",
]


def file_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_raw(path: Path = RAW_CSV) -> pd.DataFrame:
    """Load the raw CSV, check schema and integrity, and index it by record_id."""
    if file_sha256(path) != EXPECTED_SHA256:
        raise ValueError(f"{path} does not match the pinned source checksum; raw data was modified.")

    df = pd.read_csv(path)
    missing = set(NUMERIC_COLUMNS + TEXT_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if list(df["record_id"]) != RECORD_IDS:
        raise ValueError(f"Unexpected records: {list(df['record_id'])}")
    if df[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("Numeric columns contain missing values")

    return df.set_index("record_id")
