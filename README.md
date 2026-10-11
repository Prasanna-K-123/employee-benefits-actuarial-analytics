# Actuarial Risk Modelling — Employee Benefits & Stochastic Reserving

## Registered predictive uncertainty review - 2026-10-11

[Read the predictive/calibration review](docs/PREDICTIVE_UNCERTAINTY_REVIEW.md) · [Frozen protocol](reference/predictive_reserving/PROTOCOL.json) · [Complete result summary](outputs/predictive_reserving/summary.json) · [Simulation cases](outputs/predictive_reserving/calibration_cases.csv)

Six public benchmark measures give **123 later-diagonal cells** and **23 eligible diagonal sums**. The same 22 inspected RAA predictions remain intact. Point forecasts beat no-development MAE on each measure, but nominal 95% moment intervals cover only **8/26 ABC cells**, **12/22 USAA incurred cells**, and **0/4 USAA paid eligible diagonal sums**. Public counts are dependent retrospective diagnostics, not observed final-reserve calibration.

A fixed **1,024-case simulation study** compares normal/lognormal Mack moments and shared-factor gamma/lognormal approximations, separating process and shared parameter risk. Under simulated shared calendar risk, nominal 95% coverage is only **79.3-83.6%**. One gamma training case fails all four methods and stays in the denominator. USAA incurred's negative development, negative normal endpoints, numerical gamma zeros and deterministic tail sensitivity are retained.

**37 tests** plus exact-source/public-result/design/score verification and 16 fixed simulation-case replays. Shared-factor simulation is a stated moment heuristic, not a validated bootstrap, posterior, regulatory-capital model or client reserve. See the review for assumptions, all adverse results, computational amendments and reproduction.

[![Registered Predictive Reserving](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/predictive-reserving.yml/badge.svg)](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/predictive-reserving.yml)


## Evidence release — 2026-10-09

[Published RAA reserves and uncertainty](outputs/stochastic_reserving/summary.json) · [Later-diagonal evaluation](outputs/stochastic_reserving/diagonal_backtest.csv) · [Independent Mack implementation](src/stochastic_reserving.py)

The 55-cell public reinsurance triangle gives IBNR 52,135.23 and aggregate Mack standard error 26,909.01 in the original published units. Nine external rounded standard-error values reconcile within one unit. On 22 eligible later-diagonal cells, chain-ladder MAE is 1,885.21 versus 3,425.45 for no development. This is a retrospective benchmark replication, not a calibrated health reserve. Run `python -m src.stochastic_reserving`; the expanded model suite has 12 passing tests.

[Research scope and next extension](docs/EVIDENCE_REVIEW.md)

---

[![Employee Benefits Actuarial CI](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/employee-benefits-actuarial-ci.yml/badge.svg)](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/employee-benefits-actuarial-ci.yml)

The benefits workbook below uses **synthetic employee and health-claims data**. A formula-driven Excel workbook and a separate Python calculation layer demonstrate retirement liability proxies, benefit-start cash flows, claims development, IBNR, illustrative PAD and assumption sensitivity. The separate Mack reserving extension above uses the published **RAA reinsurance triangle**; its benchmark results are not health-client valuations.

**Start here:** [Download the Excel workbook](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/raw/refs/heads/main/Employee_Benefits_Actuarial_Model.xlsx) · [Model review](docs/MODEL_REVIEW.md) · [Methodology and limitations](docs/METHODOLOGY_AND_LIMITATIONS.md) · [CI and rebuilt workbook](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/employee-benefits-actuarial-ci.yml)

## Results

| Module | Synthetic inputs | Illustrative results |
|---|---|---|
| Retirement | 180 employees; 5% pre-retirement discount rate; 4% salary growth | **$25.27m liability proxy**; **$30.37m at 4%** and **$21.21m at 6%** |
| Health & welfare | 12 × 12 cumulative paid-claims triangle | **$14.81m ultimate claims**; **$3.06m IBNR**; **$3.22m reserve proxy** including 5% PAD |
| Claims trend | 5% / 7% / 9% annual trend | **$15.55m / $15.85m / $16.15m** next-year cost proxies |

All amounts are illustrative USD. The retirement sensitivity changes the pre-retirement discount rate while holding the separate 4% annuity rate fixed. These are model assumptions, not market-calibrated or regulatory assumptions.

## Review the evidence

- [Formula-driven workbook](Employee_Benefits_Actuarial_Model.xlsx): editable assumptions, employee-level pension calculations and total liability proxy, claims development factors, IBNR/PAD and claim-trend scenarios.
- [Python model](src/model.py) and [Excel builder](src/build_excel.py).
- [Workbook formula map](docs/WORKBOOK_FORMULA_MAP.md).
- [Summary](outputs/summary.json), [retirement sensitivities](outputs/pension_sensitivity.csv), [15-year benefit-start forecast](outputs/pension_cashflow_forecast.csv), and [health sensitivities](outputs/health_claims_sensitivity.csv).
- [Eight model controls](tests/test_model.py) plus [workbook evidence checks](src/verify_workbook.py).

The retirement scenario comparison, benefit-start forecast and simplified lump-sum illustration are Python/CSV outputs. Change the workbook's retirement assumptions to inspect an individual scenario. The benefit-start schedule shows newly commencing annual benefits; it is not the plan's full annual payment stream.

## Reproduce

From this repository's root, using Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m src.model
python -m pytest -q
python -m src.build_excel
```

The model regenerates both synthetic input files and output evidence. The builder regenerates the workbook with live formulas. Open the rebuilt file in Excel or LibreOffice to calculate formulas: openpyxl writes formulas but does not evaluate them.

CI runs the eight model controls, checks the committed workbook's cached totals against Python, rebuilds and compares formulas/inputs, then recalculates the rebuilt workbook with LibreOffice and checks its results. The recalculated workbook is also available as a workflow artifact. The committed download above does not require an artifact download or GitHub sign-in.

## Limitations

This is **not PwC/client work, actuarial-industry tenure, a qualified pension valuation, a booked reserve or production deployment**. It does not establish actuarial society membership or examination progress.

The retirement proxy omits mortality, turnover, plan-specific rules, assets and funding/accounting requirements; it is not an ASC 715 / IAS 19 / ERISA / IRS valuation. The health triangle has a common deterministic development pattern, making it a mechanics demonstration rather than evidence of predictive accuracy. The 5% PAD is illustrative, not a calibrated confidence margin. The annual trend proxy assumes a comparable exposure base and does not model enrollment or benefit changes.

## Project provenance

This is the standalone continuation of the [original project in the profile repository](https://github.com/Prasanna-K-123/Prasanna-K-123/tree/5ca25bdc21308c02def796b85ba45cf7d4aae5a5/workforce-solutions-actuarial-analytics). The original evidence and history remain intact. The core Python model, synthetic seed, eight controls and headline results are preserved. This release adds a direct workbook download and workbook checks, corrects the years-to-retirement format, adds the pension total and selected-trend output, and handles a zero annuity rate.
