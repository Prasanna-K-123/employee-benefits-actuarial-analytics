# Methodology and limitations

This is an **educational employee-benefits actuarial analytics project** using deterministic synthetic data. It does not represent client work, employer experience, an actuarial opinion or a production valuation.

## Retirement module
The model projects salary to age 65, applies an illustrative 1.5% accrual rate to current service, values a fixed 15-year annuity proxy at retirement and discounts the result to the valuation date. Sensitivities vary discount rate and salary growth.

The output is deliberately called a **liability proxy**, not an ASC 715, IAS 19, ERISA, IRS or qualified actuarial valuation. It omits plan-specific terms, mortality/decrements, turnover, optional forms, taxes, assets, service/interest cost, actuarial gains/losses and funding rules.

## Health & welfare module
A synthetic 12x12 cumulative paid-claims triangle is evaluated with a basic chain-ladder method to estimate ultimate claims and IBNR. A 5% illustrative PAD / risk margin and 5%/7%/9% claim-trend scenarios are used for sensitivity analysis.

This is not a booked reserve or accounting opinion and does not claim GAAP/statutory compliance, State Page or Supplemental Health Care Exhibit reporting, value-based-care accrual methodology, or PDR estimation.

The point is to demonstrate liability measurement, cash-flow/claims reasoning, sensitivity testing, assumption governance and transparent model limitations without manufacturing actuarial industry experience.

