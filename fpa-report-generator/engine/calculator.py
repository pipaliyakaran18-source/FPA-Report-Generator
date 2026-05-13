"""Variance calculator for FP&A reporting.

Takes Actual vs Budget for eight P&L line items (Revenue, COGS, Gross
Profit, OpEx, EBITDA, D&A, EBIT, Net Income) and produces a single
``FinancialAnalysis`` dataclass containing per-line variance amounts,
variance percentages, a favourable / adverse classification, and the
key margin and cost ratios used downstream by the commentary engine
and the Word report builder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Direction = Literal["Favourable", "Adverse", "Neutral"]

# Lines where being above budget is good news.
_REVENUE_LIKE: frozenset[str] = frozenset(
    {"Revenue", "Gross Profit", "EBITDA", "EBIT", "Net Income"}
)
# Lines where being below budget is good news.
_COST_LIKE: frozenset[str] = frozenset({"COGS", "OpEx", "D&A"})


@dataclass
class LineItem:
    """Variance result for a single P&L line.

    Attributes:
        name: Label used in the variance table and commentary.
        actual: Reported actual value, in the report's display unit.
        budget: Budgeted value, in the same unit as ``actual``.
        variance_amount: ``actual - budget`` (positive means above budget).
        variance_pct: ``(actual - budget) / budget`` expressed as a
            fraction. Zero when ``budget`` is zero to avoid division
            errors.
        direction: ``"Favourable"`` when the variance helps earnings,
            ``"Adverse"`` when it hurts, ``"Neutral"`` when zero.
    """

    name: str
    actual: float
    budget: float
    variance_amount: float
    variance_pct: float
    direction: Direction


@dataclass
class FinancialAnalysis:
    """Full variance and ratio analysis for one reporting period.

    Holds the eight line-item variances plus four key ratios — gross
    margin, EBITDA margin, net margin, and cost ratio — each given in
    Actual, Budget, and ``delta_pp`` (percentage-point) form.
    """

    revenue: LineItem
    cogs: LineItem
    gross_profit: LineItem
    opex: LineItem
    ebitda: LineItem
    da: LineItem
    ebit: LineItem
    net_income: LineItem

    gross_margin_actual: float
    gross_margin_budget: float
    gross_margin_delta_pp: float

    ebitda_margin_actual: float
    ebitda_margin_budget: float
    ebitda_margin_delta_pp: float

    net_margin_actual: float
    net_margin_budget: float
    net_margin_delta_pp: float

    cost_ratio_actual: float
    cost_ratio_budget: float
    cost_ratio_delta_pp: float

    @property
    def line_items(self) -> list[LineItem]:
        """Return the eight line items in income-statement order."""
        return [
            self.revenue,
            self.cogs,
            self.gross_profit,
            self.opex,
            self.ebitda,
            self.da,
            self.ebit,
            self.net_income,
        ]


def _direction(name: str, variance: float) -> Direction:
    """Classify a variance as Favourable / Adverse / Neutral.

    Revenue- and profit-like lines are favourable when the variance is
    positive; cost-like lines are favourable when the variance is
    negative. A zero variance is treated as neutral.
    """
    if variance == 0:
        return "Neutral"
    if name in _REVENUE_LIKE:
        return "Favourable" if variance > 0 else "Adverse"
    if name in _COST_LIKE:
        return "Favourable" if variance < 0 else "Adverse"
    return "Neutral"


def _line(name: str, actual: float, budget: float) -> LineItem:
    """Build a single ``LineItem`` from raw actual / budget values."""
    variance = actual - budget
    pct = (variance / budget) if budget else 0.0
    return LineItem(
        name=name,
        actual=actual,
        budget=budget,
        variance_amount=variance,
        variance_pct=pct,
        direction=_direction(name, variance),
    )


def _ratio_pair(
    num_actual: float,
    den_actual: float,
    num_budget: float,
    den_budget: float,
) -> tuple[float, float, float]:
    """Return ``(actual_ratio, budget_ratio, delta_in_percentage_points)``."""
    a = num_actual / den_actual if den_actual else 0.0
    b = num_budget / den_budget if den_budget else 0.0
    return a, b, (a - b) * 100.0


def analyse(
    *,
    revenue_actual: float,
    revenue_budget: float,
    cogs_actual: float,
    cogs_budget: float,
    gross_profit_actual: float,
    gross_profit_budget: float,
    opex_actual: float,
    opex_budget: float,
    ebitda_actual: float,
    ebitda_budget: float,
    da_actual: float,
    da_budget: float,
    ebit_actual: float,
    ebit_budget: float,
    net_income_actual: float,
    net_income_budget: float,
) -> FinancialAnalysis:
    """Compute the full variance + ratio pack from the eight line items.

    All amounts must be supplied in the same currency and unit (the
    convention used elsewhere in this project is millions). Both the
    actual and the budget value are required for each line.

    Args:
        revenue_actual: Reported top-line revenue.
        revenue_budget: Budgeted top-line revenue.
        cogs_actual: Reported cost of goods sold.
        cogs_budget: Budgeted cost of goods sold.
        gross_profit_actual: Revenue minus COGS, actual.
        gross_profit_budget: Revenue minus COGS, budget.
        opex_actual: Operating expenses below the gross-profit line.
        opex_budget: Budgeted operating expenses.
        ebitda_actual: Earnings before interest, tax, D&A.
        ebitda_budget: Budgeted EBITDA.
        da_actual: Depreciation and amortisation.
        da_budget: Budgeted D&A.
        ebit_actual: EBITDA minus D&A.
        ebit_budget: Budgeted EBIT.
        net_income_actual: Bottom-line earnings.
        net_income_budget: Budgeted net income.

    Returns:
        Populated ``FinancialAnalysis`` ready for the commentary engine
        and the Word builder.
    """
    revenue = _line("Revenue", revenue_actual, revenue_budget)
    cogs = _line("COGS", cogs_actual, cogs_budget)
    gross_profit = _line("Gross Profit", gross_profit_actual, gross_profit_budget)
    opex = _line("OpEx", opex_actual, opex_budget)
    ebitda = _line("EBITDA", ebitda_actual, ebitda_budget)
    da = _line("D&A", da_actual, da_budget)
    ebit = _line("EBIT", ebit_actual, ebit_budget)
    net_income = _line("Net Income", net_income_actual, net_income_budget)

    gm_a, gm_b, gm_d = _ratio_pair(
        gross_profit_actual, revenue_actual,
        gross_profit_budget, revenue_budget,
    )
    em_a, em_b, em_d = _ratio_pair(
        ebitda_actual, revenue_actual,
        ebitda_budget, revenue_budget,
    )
    nm_a, nm_b, nm_d = _ratio_pair(
        net_income_actual, revenue_actual,
        net_income_budget, revenue_budget,
    )
    cr_a, cr_b, cr_d = _ratio_pair(
        cogs_actual, revenue_actual,
        cogs_budget, revenue_budget,
    )

    return FinancialAnalysis(
        revenue=revenue,
        cogs=cogs,
        gross_profit=gross_profit,
        opex=opex,
        ebitda=ebitda,
        da=da,
        ebit=ebit,
        net_income=net_income,
        gross_margin_actual=gm_a,
        gross_margin_budget=gm_b,
        gross_margin_delta_pp=gm_d,
        ebitda_margin_actual=em_a,
        ebitda_margin_budget=em_b,
        ebitda_margin_delta_pp=em_d,
        net_margin_actual=nm_a,
        net_margin_budget=nm_b,
        net_margin_delta_pp=nm_d,
        cost_ratio_actual=cr_a,
        cost_ratio_budget=cr_b,
        cost_ratio_delta_pp=cr_d,
    )
