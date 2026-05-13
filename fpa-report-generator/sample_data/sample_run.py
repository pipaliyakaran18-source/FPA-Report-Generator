"""End-to-end smoke test using Apple Inc. Q1 FY2026 pre-filled data.

Runs calculator → commentary → Word builder without prompting and
saves the resulting ``.docx`` into ``output/``.

Usage:
    python -m sample_data.sample_run
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sibling packages importable when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.calculator import analyse
from engine.commentary import generate
from report.word_builder import build_report

# Apple Inc. Q1 FY2026 (USD billions, presented in the report as "m").
REVENUE_ACTUAL, REVENUE_BUDGET = 124.3, 119.0
COGS_ACTUAL, COGS_BUDGET = 54.9, 53.5
OPEX_ACTUAL, OPEX_BUDGET = 14.5, 15.0
EBITDA_ACTUAL, EBITDA_BUDGET = 54.9, 50.5
DA_ACTUAL, DA_BUDGET = 3.2, 3.0
NET_INCOME_ACTUAL, NET_INCOME_BUDGET = 36.3, 33.5

GROSS_PROFIT_ACTUAL = REVENUE_ACTUAL - COGS_ACTUAL
GROSS_PROFIT_BUDGET = REVENUE_BUDGET - COGS_BUDGET
EBIT_ACTUAL = EBITDA_ACTUAL - DA_ACTUAL
EBIT_BUDGET = EBITDA_BUDGET - DA_BUDGET

COMPANY = "Apple Inc."
PERIOD = "Q1 FY2026"
ANALYST = "FP&A Team"
CURRENCY = "$"


def main() -> Path:
    """Run the pipeline and return the path to the saved Word file."""
    analysis = analyse(
        revenue_actual=REVENUE_ACTUAL,
        revenue_budget=REVENUE_BUDGET,
        cogs_actual=COGS_ACTUAL,
        cogs_budget=COGS_BUDGET,
        gross_profit_actual=GROSS_PROFIT_ACTUAL,
        gross_profit_budget=GROSS_PROFIT_BUDGET,
        opex_actual=OPEX_ACTUAL,
        opex_budget=OPEX_BUDGET,
        ebitda_actual=EBITDA_ACTUAL,
        ebitda_budget=EBITDA_BUDGET,
        da_actual=DA_ACTUAL,
        da_budget=DA_BUDGET,
        ebit_actual=EBIT_ACTUAL,
        ebit_budget=EBIT_BUDGET,
        net_income_actual=NET_INCOME_ACTUAL,
        net_income_budget=NET_INCOME_BUDGET,
    )

    commentary = generate(
        analysis,
        company=COMPANY,
        period=PERIOD,
        currency=CURRENCY,
    )

    safe_period = PERIOD.replace(" ", "_")
    safe_company = COMPANY.replace(" ", "_").replace(".", "")
    output_path = PROJECT_ROOT / "output" / f"{safe_company}_{safe_period}_Variance_Report.docx"

    saved = build_report(
        analysis=analysis,
        commentary=commentary,
        company=COMPANY,
        period=PERIOD,
        analyst=ANALYST,
        currency=CURRENCY,
        output_path=output_path,
    )
    print(f"Report saved to: {saved}")
    return saved


if __name__ == "__main__":
    main()
