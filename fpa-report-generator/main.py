"""Entry point for the FP&A report generator.

Running ``python main.py`` launches the interactive terminal UI,
collects the figures, runs the calculator, generates the five-paragraph
commentary, renders the Word report, and prints the saved file path.

Add ``--sample`` to run the Apple Q1 FY2026 pipeline non-interactively.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

from engine.calculator import analyse
from engine.commentary import generate
from report.word_builder import build_report
from ui.terminal import collect_inputs, confirm_generate, render_summary

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def _safe_filename(company: str, period: str) -> str:
    safe_company = "".join(c for c in company if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_period = "".join(c for c in period if c.isalnum() or c in " _-").strip().replace(" ", "_")
    return f"{safe_company}_{safe_period}_Variance_Report.docx"


def run_interactive() -> Path | None:
    """Run the full UI → calculator → commentary → Word pipeline."""
    console = Console()
    inputs = collect_inputs(console=console)

    analysis = analyse(**inputs.as_calculator_kwargs())
    render_summary(inputs, analysis, console=console)

    if not confirm_generate(console=console):
        console.print("[yellow]Cancelled — no report generated.[/yellow]")
        return None

    commentary = generate(
        analysis,
        company=inputs.company,
        period=inputs.period,
        currency=inputs.currency,
    )

    output_path = OUTPUT_DIR / _safe_filename(inputs.company, inputs.period)
    saved = build_report(
        analysis=analysis,
        commentary=commentary,
        company=inputs.company,
        period=inputs.period,
        analyst=inputs.analyst,
        currency=inputs.currency,
        output_path=output_path,
    )
    console.print(f"\n[bold green]Report saved to:[/bold green] {saved}")
    return saved


def run_sample() -> Path:
    """Run the bundled Apple Q1 FY2026 pipeline."""
    from sample_data.sample_run import main as sample_main

    return sample_main()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FP&A variance report generator (Word output)."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Skip the UI and run the bundled Apple Q1 FY2026 sample.",
    )
    args = parser.parse_args(argv)

    try:
        if args.sample:
            run_sample()
        else:
            run_interactive()
    except KeyboardInterrupt:
        Console().print("\n[yellow]Aborted by user.[/yellow]")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
