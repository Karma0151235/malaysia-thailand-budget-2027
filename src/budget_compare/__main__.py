"""Run the full pipeline: validate data, compute findings, draw charts."""

from budget_compare import OUTPUT_DIR
from budget_compare.charts import draw_all
from budget_compare.data import load_raw
from budget_compare.metrics import compute_findings, write_findings
from budget_compare.references import draw_references
from budget_compare.style import apply_theme


def main() -> None:
    """Entry point for `python -m budget_compare`."""
    df = load_raw()
    findings = compute_findings(df)
    write_findings(findings, OUTPUT_DIR / "findings.json")
    print(f"Wrote {OUTPUT_DIR / 'findings.json'}")

    apply_theme()
    for path in [*draw_all(findings, OUTPUT_DIR / "charts"), *draw_references(OUTPUT_DIR)]:
        print(f"Wrote {path.relative_to(OUTPUT_DIR.parent)}")


if __name__ == "__main__":
    main()
