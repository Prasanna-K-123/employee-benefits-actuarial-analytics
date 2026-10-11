# Current predictive extension - 2026-10-11

[Full predictive uncertainty review](PREDICTIVE_UNCERTAINTY_REVIEW.md), [registered source/design](../reference/predictive_reserving/PROTOCOL.json) and [complete evidence](../outputs/predictive_reserving/summary.json) extend the same actuarial family. Six public measures, 123 known later-diagonal cells and 1,024 controlled cases expose weak nominal coverage and calendar/tail sensitivity. All original RAA references, 22 inspected predictions and benefits workbook are retained. No new untouched public holdout, coverage guarantee, client valuation or third-party review is claimed.

The defined comparison is complete. Dispersion uncertainty, validated calendar-aware/higher-moment alternatives, independent insurer/vintage evidence, mortality/turnover and real benefit rules remain substantive gaps. The earlier note below keeps its historical scope.

---

# Evidence review: Actuarial Risk Modelling

Independent portfolio research. Updated 2026-10-09. Development and documentation include AI assistance; the committed executable code, data provenance and test outputs establish the work products. No institutional endorsement or third-party authorship review is claimed.

## Research purpose

Employee benefits, claims reserving and uncertainty.

## Published evidence

Published RAA triangle; independently reproduced 9 rounded Mack standard errors; 22 later-diagonal forecasts; Excel/Python benefits model.

## Interpretation boundary

RAA is a historical reinsurance benchmark, not health-client data. Benefits valuation uses synthetic proxies and is not an IAS 19/ASC 715 valuation.

## Review standard

Check the source data and split before interpreting a score. Compare the strongest result with a simple baseline. Inspect failed diagnostics and uncertainty. Reproduce the calculations from the documented environment; distinguish measured findings from simulated or assumed scenarios. The tests cover specific documented invariants and do not establish complete production correctness.

## Next research extension

Replicate across several heterogeneous public claims triangles and evaluate distributional reserve uncertainty, calendar effects and tail sensitivity. Add mortality/turnover and explicit benefit rules before making a qualified pension-valuation claim.
