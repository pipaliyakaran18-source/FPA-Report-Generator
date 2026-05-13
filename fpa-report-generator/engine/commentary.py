"""Adaptive prose commentary engine.

Takes a ``FinancialAnalysis`` and produces five paragraphs of formal
management commentary. Each paragraph references the real numbers from
the analysis and switches its narrative depending on whether the
underlying variances were favourable or adverse. Minimum length per
paragraph is 80 words; no bullet points are used.
"""

from __future__ import annotations

from dataclasses import dataclass

from .calculator import FinancialAnalysis, LineItem


@dataclass
class Commentary:
    """Five paragraphs of management commentary, ordered for the report."""

    executive_summary: str
    revenue_and_gross_profit: str
    opex_and_ebitda: str
    net_income: str
    outlook: str

    def as_paragraphs(self) -> list[tuple[str, str]]:
        """Return ``(heading, body)`` pairs in report order."""
        return [
            ("Executive Summary", self.executive_summary),
            ("Revenue & Gross Profit", self.revenue_and_gross_profit),
            ("OpEx & EBITDA", self.opex_and_ebitda),
            ("Net Income", self.net_income),
            ("Outlook", self.outlook),
        ]


def _money(currency: str, value: float) -> str:
    """Format a value as e.g. ``$124.3m``. Preserves sign for negatives."""
    sign = "-" if value < 0 else ""
    return f"{sign}{currency}{abs(value):,.1f}m"


def _pct(value: float) -> str:
    """Format a fractional variance, e.g. ``0.045`` -> ``+4.5%``."""
    return f"{value * 100:+.1f}%"


def _pp(value: float) -> str:
    """Format a percentage-point delta, e.g. ``1.4`` -> ``+1.4pp``."""
    return f"{value:+.1f}pp"


def _fav(item: LineItem) -> bool:
    return item.direction == "Favourable"


def _tone(item: LineItem, favourable: str, adverse: str, neutral: str) -> str:
    if item.direction == "Favourable":
        return favourable
    if item.direction == "Adverse":
        return adverse
    return neutral


def _executive_summary(
    a: FinancialAnalysis, company: str, period: str, ccy: str
) -> str:
    fav = sum(1 for li in a.line_items if li.direction == "Favourable")
    adv = sum(1 for li in a.line_items if li.direction == "Adverse")
    if _fav(a.revenue) and _fav(a.ebitda):
        headline = "a strong operating performance ahead of plan on both the top and bottom lines"
    elif _fav(a.revenue) and not _fav(a.ebitda):
        headline = "revenue growth ahead of plan offset by softer operating leverage"
    elif not _fav(a.revenue) and _fav(a.ebitda):
        headline = "a resilient earnings outcome despite a top-line shortfall"
    else:
        headline = "a challenging quarter with both revenue and earnings short of budget"
    return (
        f"{company} delivered {headline} during {period}. "
        f"Reported revenue of {_money(ccy, a.revenue.actual)} compared with a "
        f"budget of {_money(ccy, a.revenue.budget)}, producing a variance of "
        f"{_money(ccy, a.revenue.variance_amount)} or {_pct(a.revenue.variance_pct)} "
        f"({a.revenue.direction.lower()}). EBITDA closed at "
        f"{_money(ccy, a.ebitda.actual)} versus a plan of {_money(ccy, a.ebitda.budget)}, "
        f"a {_pct(a.ebitda.variance_pct)} swing that translated into an EBITDA margin "
        f"of {a.ebitda_margin_actual * 100:.1f}% against a planned "
        f"{a.ebitda_margin_budget * 100:.1f}% ({_pp(a.ebitda_margin_delta_pp)}). "
        f"Net income finished at {_money(ccy, a.net_income.actual)} "
        f"({_pct(a.net_income.variance_pct)} versus plan). Of the eight tracked "
        f"line items {fav} were favourable to plan and {adv} adverse, framing "
        f"the detailed commentary that follows."
    )


def _revenue_paragraph(a: FinancialAnalysis, ccy: str) -> str:
    rev, cogs, gp = a.revenue, a.cogs, a.gross_profit
    rev_tone = _tone(
        rev,
        "outperformed budget, reflecting stronger-than-anticipated demand and "
        "favourable pricing dynamics across the principal revenue streams",
        "fell short of budget, indicating slower demand momentum and tighter "
        "pricing realisation than the plan assumed",
        "tracked precisely in line with plan, with no material upside or "
        "downside surprises versus the budgeted run rate",
    )
    cogs_tone = _tone(
        cogs,
        "came in below plan, supported by procurement discipline and improved "
        "input-cost management",
        "exceeded the budget, driven by input-cost inflation and an unfavourable "
        "mix shift that diluted unit economics",
        "landed broadly in line with the budgeted cost base",
    )
    gm_tone = (
        f"expanded by {_pp(a.gross_margin_delta_pp)} to "
        f"{a.gross_margin_actual * 100:.1f}%"
        if a.gross_margin_delta_pp > 0
        else f"compressed by {_pp(a.gross_margin_delta_pp)} to "
        f"{a.gross_margin_actual * 100:.1f}%"
        if a.gross_margin_delta_pp < 0
        else f"held flat at {a.gross_margin_actual * 100:.1f}%"
    )
    return (
        f"Revenue of {_money(ccy, rev.actual)} {rev_tone}, representing a "
        f"variance of {_money(ccy, rev.variance_amount)} or "
        f"{_pct(rev.variance_pct)} against a budget of "
        f"{_money(ccy, rev.budget)}. Cost of goods sold of "
        f"{_money(ccy, cogs.actual)} {cogs_tone}, "
        f"a {_pct(cogs.variance_pct)} movement relative to the planned "
        f"{_money(ccy, cogs.budget)}. The combined effect produced gross "
        f"profit of {_money(ccy, gp.actual)} ({_pct(gp.variance_pct)} versus "
        f"a budgeted {_money(ccy, gp.budget)}), while the gross margin "
        f"{gm_tone} against the planned {a.gross_margin_budget * 100:.1f}%. "
        f"The gross-profit outcome is therefore classified as "
        f"{gp.direction.lower()} for variance-reporting purposes."
    )


def _opex_ebitda_paragraph(a: FinancialAnalysis, ccy: str) -> str:
    opex, ebitda = a.opex, a.ebitda
    opex_tone = _tone(
        opex,
        "demonstrated firm cost discipline, with operating expenses held "
        "below the budgeted envelope despite the underlying activity level",
        "ran ahead of the budgeted envelope, reflecting elevated discretionary "
        "spend and softer operating leverage than the plan contemplated",
        "tracked the budgeted envelope precisely",
    )
    em_tone = (
        f"expanded by {_pp(a.ebitda_margin_delta_pp)} to "
        f"{a.ebitda_margin_actual * 100:.1f}%"
        if a.ebitda_margin_delta_pp > 0
        else f"compressed by {_pp(a.ebitda_margin_delta_pp)} to "
        f"{a.ebitda_margin_actual * 100:.1f}%"
        if a.ebitda_margin_delta_pp < 0
        else f"held flat at {a.ebitda_margin_actual * 100:.1f}%"
    )
    return (
        f"Operating expenses of {_money(ccy, opex.actual)} {opex_tone}, a "
        f"{_pct(opex.variance_pct)} variance against the planned "
        f"{_money(ccy, opex.budget)}. Combined with the gross-profit "
        f"outcome, this produced EBITDA of {_money(ccy, ebitda.actual)} "
        f"versus a budget of {_money(ccy, ebitda.budget)} — a variance of "
        f"{_money(ccy, ebitda.variance_amount)} or "
        f"{_pct(ebitda.variance_pct)}, classified as "
        f"{ebitda.direction.lower()}. The EBITDA margin {em_tone} relative "
        f"to the planned {a.ebitda_margin_budget * 100:.1f}%, while the COGS-to-"
        f"revenue cost ratio of {a.cost_ratio_actual * 100:.1f}% compared "
        f"with a budgeted {a.cost_ratio_budget * 100:.1f}% "
        f"({_pp(a.cost_ratio_delta_pp)}). Together these movements describe "
        f"the quality of the underlying operating performance."
    )


def _net_income_paragraph(a: FinancialAnalysis, ccy: str) -> str:
    da, ebit, ni = a.da, a.ebit, a.net_income
    da_tone = _tone(
        da,
        "depreciation and amortisation ran modestly below plan, providing a "
        "small tailwind to the operating result",
        "depreciation and amortisation came in above plan, creating a modest "
        "headwind below EBITDA",
        "depreciation and amortisation tracked precisely in line with plan",
    )
    ni_tone = _tone(
        ni,
        "exceeded the budgeted level, supported by the favourable operating "
        "drop-through and disciplined below-the-line items",
        "fell short of the budgeted level, with the operating shortfall "
        "compounded by below-the-line effects",
        "matched the budgeted level almost exactly",
    )
    return (
        f"Below the EBITDA line, {da_tone}: {_money(ccy, da.actual)} versus "
        f"a planned {_money(ccy, da.budget)} ({_pct(da.variance_pct)}). "
        f"EBIT therefore closed at {_money(ccy, ebit.actual)} against a "
        f"budgeted {_money(ccy, ebit.budget)}, a variance of "
        f"{_money(ccy, ebit.variance_amount)} or {_pct(ebit.variance_pct)} "
        f"({ebit.direction.lower()}). Net income of {_money(ccy, ni.actual)} "
        f"{ni_tone}, representing a {_pct(ni.variance_pct)} variance against "
        f"the planned {_money(ccy, ni.budget)}. Net margin of "
        f"{a.net_margin_actual * 100:.1f}% compares with a planned "
        f"{a.net_margin_budget * 100:.1f}% ({_pp(a.net_margin_delta_pp)}), "
        f"completing the walk from top-line revenue down to the bottom-line "
        f"earnings outcome reported for the period."
    )


def _outlook_paragraph(a: FinancialAnalysis, company: str, ccy: str) -> str:
    rev, ebitda, ni = a.revenue, a.ebitda, a.net_income
    if _fav(rev) and _fav(ebitda) and _fav(ni):
        stance = (
            "Management views the result as a constructive foundation for the "
            "remainder of the year. The combination of favourable revenue, "
            "EBITDA and net-income outcomes points to sustained operating "
            "momentum, and the priority is to convert this strength into "
            "raised full-year guidance once the second quarter has been "
            "closed and reviewed"
        )
    elif not _fav(rev) and not _fav(ebitda):
        stance = (
            "Management is treating the result as a clear call to action. "
            "Top-line and earnings shortfalls of this magnitude warrant a "
            "tightening of discretionary spend, a refresh of demand "
            "assumptions in the latest forecast and an accelerated review of "
            "the cost base to protect margin in the remaining quarters"
        )
    else:
        stance = (
            "Management regards the result as mixed but manageable. The "
            "favourable and adverse variances broadly offset one another at "
            "the EBITDA level, and the focus for the coming quarter is to "
            "consolidate the areas of strength while addressing the specific "
            "line items that drove the adverse movements without changing "
            "the headline full-year framework"
        )
    return (
        f"{stance}. On the current trajectory, run-rate revenue of roughly "
        f"{_money(ccy, rev.actual * 4)} and run-rate EBITDA of "
        f"{_money(ccy, ebitda.actual * 4)} provide a useful, if simplistic, "
        f"reference for the annualised picture. {company} will reconfirm its "
        f"full-year guidance at the next scheduled trading update, and the "
        f"FP&A team will continue to monitor the cost ratio "
        f"({a.cost_ratio_actual * 100:.1f}% this period) and EBITDA margin "
        f"({a.ebitda_margin_actual * 100:.1f}%) as the primary leading "
        f"indicators of underlying profitability."
    )


def generate(
    analysis: FinancialAnalysis,
    *,
    company: str,
    period: str,
    currency: str = "$",
) -> Commentary:
    """Produce the five-paragraph management commentary.

    Args:
        analysis: Output of :func:`engine.calculator.analyse`.
        company: Reporting entity name, e.g. ``"Apple Inc."``.
        period: Reporting period label, e.g. ``"Q1 FY2026"``.
        currency: Currency symbol used in money values, e.g. ``"$"``.

    Returns:
        A :class:`Commentary` instance with five populated paragraphs.
    """
    return Commentary(
        executive_summary=_executive_summary(analysis, company, period, currency),
        revenue_and_gross_profit=_revenue_paragraph(analysis, currency),
        opex_and_ebitda=_opex_ebitda_paragraph(analysis, currency),
        net_income=_net_income_paragraph(analysis, currency),
        outlook=_outlook_paragraph(analysis, company, currency),
    )
