# Model review - decision interpretation

This note interprets the synthetic model outputs as an analyst would review them. It is educational portfolio work, not a professional actuarial opinion or client deliverable.

## Retirement module

Base liability proxy: **$25.27m** at a 5% discount rate and 4% salary growth.

- A 100 bps lower discount rate raises the proxy to **$30.37m**, approximately **+20.2%** versus base.
- A 100 bps higher discount rate lowers it to **$21.21m**, approximately **-16.1%** versus base.
- Salary-growth sensitivity is directionally consistent: higher assumed future salary growth increases the modeled benefit obligation.
- The 15-year benefit-start forecast makes the timing of newly commencing annual benefits visible rather than reporting only a single present-value number.
- The illustrative lump-sum scenario is intentionally simplified. It demonstrates de-risking mechanics, not transaction pricing or plan-termination accounting.

**Interpretation:** the liability proxy is highly assumption-sensitive, so a reviewer should focus on assumption governance and scenario ranges rather than a single point estimate.

## Health & welfare module

- Paid claims observed to date: **$11.75m**.
- Estimated ultimate claims: **$14.81m**.
- Chain-ladder IBNR: **$3.06m**, approximately **20.7%** of estimated ultimate claims.
- Illustrative 5% PAD / risk margin: **$0.15m**.
- Reserve-with-PAD proxy: **$3.22m**, approximately **21.7%** of estimated ultimate claims.
- 5% / 7% / 9% trend assumptions move the next-year cost proxy from approximately **$15.55m** to **$16.15m**.

**Interpretation:** development and trend assumptions materially affect projected cost. The correct professional response would require plan-specific claim history, benefit design, enrollment, utilization, network and accounting/statutory context; this synthetic example does not pretend to supply those inputs.

## Review controls

- inputs and formulas are separated in the Excel model;
- the Python layer independently recomputes the core results;
- automated tests check directional sensitivities and non-negativity controls;
- limitations are stated before interpretation;
- no result is described as a booked reserve, ASC 715 / IAS 19 valuation, statutory filing or client conclusion.

