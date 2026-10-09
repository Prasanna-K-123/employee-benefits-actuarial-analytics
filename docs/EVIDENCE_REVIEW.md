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
