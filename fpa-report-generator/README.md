# FP&A Report Generator

A Python tool that turns a single period of Actual-vs-Budget figures into a
formal four-page Word variance report, complete with auto-written management
commentary.

## Pipeline

```
Terminal UI  →  Calculator  →  Commentary engine  →  Word builder  →  .docx
   (rich +        (variances,     (5 adaptive               (python-docx,
    questionary)   ratios)         paragraphs)               4 pages, shaded)
```

## Project structure

```
fpa-report-generator/
├── main.py                      # entry point (interactive UI by default)
├── engine/
│   ├── calculator.py            # variance + ratio dataclass
│   └── commentary.py            # 5-paragraph prose generator
├── report/
│   └── word_builder.py          # python-docx report builder
├── ui/
│   └── terminal.py              # rich + questionary input + preview table
├── sample_data/
│   └── sample_run.py            # Apple Q1 FY2026 end-to-end smoke test
├── output/                      # generated .docx files land here
├── requirements.txt
└── README.md
```

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run interactively

```powershell
python main.py
```

The terminal UI collects:

- Company name, reporting period, analyst name, currency symbol
- Actual and Budget values for eight line items: Revenue, COGS, Gross Profit,
  OpEx, EBITDA, D&A, EBIT, Net Income

It then renders a colour-coded preview (green = favourable, red = adverse,
yellow = neutral). After confirming, the Word file is written to
`output/<Company>_<Period>_Variance_Report.docx`.

## Run the bundled sample

Apple Inc. Q1 FY2026 figures are pre-filled in `sample_data/sample_run.py`.

```powershell
python main.py --sample
# or, equivalently:
python -m sample_data.sample_run
```

## What's in the Word report

1. **Cover page** — company, period, analyst, `CONFIDENTIAL` banner, date.
2. **Variance table** — eight line items with red/green cell shading, plus
   three bold margin-% rows (Gross, EBITDA, Net).
3. **Management commentary** — five paragraphs (Executive Summary, Revenue &
   Gross Profit, OpEx & EBITDA, Net Income, Outlook) with bold lead sentences
   and adaptive language driven by the favourable / adverse classification.
4. **Key ratios appendix** — Gross / EBITDA / Net margins and the cost
   ratio, with percentage-point deltas vs budget.

Every page footer shows `Company | CONFIDENTIAL | Page X`.

## Notes

- All figures are treated as millions in the user's chosen currency.
- The commentary engine adapts wording based on the direction of each
  variance. Cost-like lines (COGS, OpEx, D&A) are favourable when below
  budget; revenue and profit lines are favourable when above.
