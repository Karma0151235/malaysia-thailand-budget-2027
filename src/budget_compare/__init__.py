"""Malaysia Budget 2027 vs Thailand FY2027: reproducible comparison pipeline."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "asean_fiscal_wage_2027.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
