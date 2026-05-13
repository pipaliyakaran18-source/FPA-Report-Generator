"""Interactive terminal UI built on ``rich`` and ``questionary``.

Collects the metadata (company, period, analyst, currency) plus the
sixteen actual / budget values required by the calculator, validates
every entry, and renders a colour-coded preview table so the user can
confirm the figures before the Word report is generated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from engine.calculator import FinancialAnalysis, analyse

_QUESTIONARY_STYLE = Style(
    [
        ("qmark", "fg:#00afff bold"),
        ("question", "bold"),
        ("answer", "fg:#5fd75f bold"),
        ("pointer", "fg:#00afff bold"),
        ("highlighted", "fg:#00afff bold"),
        ("selected", "fg:#5fd75f"),
    ]
)

# Order matters: this is also the order shown in the summary table.
LINE_ITEMS: list[tuple[str, str]] = [
    ("revenue", "Revenue"),
    ("cogs", "COGS"),
    ("gross_profit", "Gross Profit"),
    ("opex", "OpEx"),
    ("ebitda", "EBITDA"),
    ("da", "D&A"),
    ("ebit", "EBIT"),
    ("net_income", "Net Income"),
]


@dataclass
class ReportInputs:
    """Everything the rest of the pipeline needs to build a report."""

    company: str
    period: str
    analyst: str
    currency: str
    values: dict[str, dict[str, float]] = field(default_factory=dict)

    def as_calculator_kwargs(self) -> dict[str, float]:
        """Flatten ``values`` into the kwargs accepted by ``analyse``."""
        out: dict[str, float] = {}
        for key, _label in LINE_ITEMS:
            out[f"{key}_actual"] = self.values[key]["actual"]
            out[f"{key}_budget"] = self.values[key]["budget"]
        return out


def _validate_nonempty(text: str) -> bool | str:
    return True if text.strip() else "Please enter a value."


def _validate_currency(text: str) -> bool | str:
    text = text.strip()
    if not text:
        return "Please enter a currency symbol."
    if len(text) > 3:
        return "Currency symbol should be at most 3 characters (e.g. $, £, €, GBP)."
    return True


def _validate_float(text: str) -> bool | str:
    try:
        float(text.replace(",", ""))
    except ValueError:
        return "Enter a number (decimals allowed, e.g. 124.3)."
    return True


def _ask_float(prompt: str, default: str | None = None) -> float:
    answer = questionary.text(
        prompt,
        default=default or "",
        validate=_validate_float,
        style=_QUESTIONARY_STYLE,
    ).ask()
    if answer is None:
        raise KeyboardInterrupt("Input cancelled.")
    return float(answer.replace(",", ""))


def collect_inputs(
    console: Console | None = None,
    *,
    defaults: ReportInputs | None = None,
) -> ReportInputs:
    """Prompt the user for every field the report needs.

    Args:
        console: Optional ``rich`` console to render banners on. A new
            one is created if not supplied.
        defaults: If supplied, the dataclass is used to pre-fill every
            prompt so the user can simply press Enter to accept.

    Returns:
        A fully populated :class:`ReportInputs`.
    """
    console = console or Console()
    console.print(
        Panel.fit(
            "[bold cyan]FP&A Variance Report Generator[/bold cyan]\n"
            "Enter the figures for the period. Numbers are in millions.",
            border_style="cyan",
        )
    )

    company = questionary.text(
        "Company name:",
        default=(defaults.company if defaults else ""),
        validate=_validate_nonempty,
        style=_QUESTIONARY_STYLE,
    ).ask()
    period = questionary.text(
        "Reporting period (e.g. Q1 FY2026):",
        default=(defaults.period if defaults else ""),
        validate=_validate_nonempty,
        style=_QUESTIONARY_STYLE,
    ).ask()
    analyst = questionary.text(
        "Analyst name:",
        default=(defaults.analyst if defaults else ""),
        validate=_validate_nonempty,
        style=_QUESTIONARY_STYLE,
    ).ask()
    currency = questionary.text(
        "Currency symbol (e.g. $, £, €):",
        default=(defaults.currency if defaults else "$"),
        validate=_validate_currency,
        style=_QUESTIONARY_STYLE,
    ).ask()

    if None in (company, period, analyst, currency):
        raise KeyboardInterrupt("Input cancelled.")

    console.print(
        "\n[bold]Enter Actual and Budget values "
        "(in millions) for each line item:[/bold]\n"
    )

    values: dict[str, dict[str, float]] = {}
    for key, label in LINE_ITEMS:
        console.rule(f"[bold cyan]{label}[/bold cyan]")
        default_actual = (
            str(defaults.values[key]["actual"]) if defaults and key in defaults.values else None
        )
        default_budget = (
            str(defaults.values[key]["budget"]) if defaults and key in defaults.values else None
        )
        actual = _ask_float(f"{label} — Actual:", default_actual)
        budget = _ask_float(f"{label} — Budget:", default_budget)
        values[key] = {"actual": actual, "budget": budget}

    return ReportInputs(
        company=company.strip(),
        period=period.strip(),
        analyst=analyst.strip(),
        currency=currency.strip(),
        values=values,
    )


def _direction_text(direction: str) -> Text:
    if direction == "Favourable":
        return Text(direction, style="bold green")
    if direction == "Adverse":
        return Text(direction, style="bold red")
    return Text(direction, style="bold yellow")


def render_summary(
    inputs: ReportInputs,
    analysis: FinancialAnalysis,
    console: Console | None = None,
) -> None:
    """Render the colour-coded preview table for user confirmation."""
    console = console or Console()
    ccy = inputs.currency

    title = (
        f"[bold]{inputs.company}[/bold]  |  {inputs.period}  |  "
        f"Analyst: {inputs.analyst}"
    )
    console.print(Panel(title, border_style="cyan"))

    table = Table(
        title="Variance Summary",
        show_lines=False,
        header_style="bold white on blue",
        title_style="bold cyan",
    )
    table.add_column("Line Item", style="bold")
    table.add_column(f"Actual ({ccy}m)", justify="right")
    table.add_column(f"Budget ({ccy}m)", justify="right")
    table.add_column(f"Variance ({ccy}m)", justify="right")
    table.add_column("Variance %", justify="right")
    table.add_column("Direction", justify="center")

    for item in analysis.line_items:
        if item.direction == "Favourable":
            row_style = "green"
        elif item.direction == "Adverse":
            row_style = "red"
        else:
            row_style = "yellow"
        table.add_row(
            item.name,
            f"{item.actual:,.1f}",
            f"{item.budget:,.1f}",
            Text(f"{item.variance_amount:+,.1f}", style=row_style),
            Text(f"{item.variance_pct * 100:+.1f}%", style=row_style),
            _direction_text(item.direction),
        )

    console.print(table)

    ratios = Table(
        title="Key Margins",
        header_style="bold white on blue",
        title_style="bold cyan",
    )
    ratios.add_column("Ratio", style="bold")
    ratios.add_column("Actual", justify="right")
    ratios.add_column("Budget", justify="right")
    ratios.add_column("Delta (pp)", justify="right")

    def _add_ratio(name: str, actual: float, budget: float, delta: float) -> None:
        style = "green" if delta > 0 else "red" if delta < 0 else "yellow"
        ratios.add_row(
            name,
            f"{actual * 100:.1f}%",
            f"{budget * 100:.1f}%",
            Text(f"{delta:+.1f}", style=style),
        )

    _add_ratio(
        "Gross Margin",
        analysis.gross_margin_actual,
        analysis.gross_margin_budget,
        analysis.gross_margin_delta_pp,
    )
    _add_ratio(
        "EBITDA Margin",
        analysis.ebitda_margin_actual,
        analysis.ebitda_margin_budget,
        analysis.ebitda_margin_delta_pp,
    )
    _add_ratio(
        "Net Margin",
        analysis.net_margin_actual,
        analysis.net_margin_budget,
        analysis.net_margin_delta_pp,
    )
    # Cost ratio: a rise is adverse, so flip the colour logic by negating delta.
    cost_delta = analysis.cost_ratio_delta_pp
    cost_style = "red" if cost_delta > 0 else "green" if cost_delta < 0 else "yellow"
    ratios.add_row(
        "Cost Ratio (COGS / Revenue)",
        f"{analysis.cost_ratio_actual * 100:.1f}%",
        f"{analysis.cost_ratio_budget * 100:.1f}%",
        Text(f"{cost_delta:+.1f}", style=cost_style),
    )

    console.print(ratios)


def confirm_generate(console: Console | None = None) -> bool:
    """Ask the user whether to proceed with Word generation."""
    console = console or Console()
    answer = questionary.confirm(
        "Generate the Word report now?",
        default=True,
        style=_QUESTIONARY_STYLE,
    ).ask()
    return bool(answer)
