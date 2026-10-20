"""Run the full pipeline: validate data, compute findings, draw charts."""

from budget_compare import OUTPUT_DIR
from budget_compare.data import load_raw
from budget_compare.metrics import compute_findings, write_findings


def main() -> None:
    """Entry point for `python -m budget_compare`."""
    df = load_raw()
    findings = compute_findings(df)
    write_findings(findings, OUTPUT_DIR / "findings.json")
    print(f"Wrote {OUTPUT_DIR / 'findings.json'}")


if __name__ == "__main__":
    main()
