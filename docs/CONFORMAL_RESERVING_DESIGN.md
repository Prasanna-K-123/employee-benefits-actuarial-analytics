# Whole-triangle predictive calibration: registered comparison

The existing predictive audit found severe undercoverage under its fixed
calendar-risk designs. This extension compares four explicit interval rules on
new draws from those already-inspected synthetic laws. It leaves every public
triangle, old prediction, old 1,024-case result and source implementation intact.

## Statistical unit and boundary

An observation is **one independently simulated whole triangle**, with its
upper observed cells as X and realized full-horizon reserve as Y. Cells and
successive public valuation diagonals are not independent calibration units.
Mack point/standard-error forecasts depend only on the observed upper triangle.
Each new calibration outcome is completed before thresholds are frozen. Test
outcomes are generated only afterwards and never enter calibration.

Calibration and evaluation use separate seed namespaces and 512/1,024 triangles
per scenario. The four laws are unchanged: independent lognormal, independent
gamma, a 10% shock at the first unobserved calendar, and rho=.35 shared-calendar
lognormal innovations. They are previously inspected designs, not new insurers,
new public outcomes or an unopened real-world period.

## Fixed methods

1. **Mack normal:** original moment interval, no calibration outcomes.
2. **Calibrated normal:** estimate mean and sample standard deviation of signed
   residual/scale on the same 512 calibration cases used by both conformal rules.
   Apply Gaussian quantiles around the bias-adjusted forecast. It is a credible
   simple calibration baseline, without a general finite-sample coverage claim.
3. **Absolute split conformal:** rank absolute reserve errors; use a common
   radius in the original units.
4. **Scaled split conformal:** rank absolute error divided by the fixed
   X-dependent Mack uncertainty scale; multiply the threshold by test scale.

All rules use the same forecasts and test cases. Methods 2–4 use the same extra
calibration labels; method 1 uses none. Additional labels/cost are disclosed,
not described as an equal-data advantage over the uncalibrated anchor. No method
or level is chosen after results. Levels 80%, 90% and 95% remain in all outputs.

For level L and n calibration cases, the rank is exactly
`ceil((n+1)*L/100)`, calculated with rational/integer arithmetic. The kth sorted
score is used without interpolation; if k>n the threshold is infinite. Ties
are accepted inclusively. For n=512 the 95% rank is 488. The conditional score
map is fixed without seeing test labels; calibration/one-test-point
exchangeability gives marginal coverage at least the rank divided by n+1.
This probability averages over calibration and the test point. It does not
certify the empirical coverage of one realized calibration batch, every
exposure subgroup, a time series or real insurer data. No continuous-score
upper coverage bound is invoked for ties/fallbacks.

Primary foundations: [Angelopoulos and Bates, sections 1 and 2.3](https://arxiv.org/abs/2107.07511)
and [Lei et al., distribution-free regression](https://www.stat.cmu.edu/~ryantibs/papers/conformal.pdf).
[Oliveira et al.](https://www.jmlr.org/papers/v25/23-1553.html) explains why
non-exchangeability requires additional assumptions/penalties; those results
are not silently applied here. This is an implementation/comparison of known
methods, not an original coverage theorem.

## Deliberate shifts, failures and efficiency

Every test law is evaluated with its own matched calibration law and with
independent-lognormal calibration. The latter is an explicit shift challenge;
no exchangeability guarantee is claimed when those laws differ. Repeated
comparisons reuse the same test draws and must not be counted as extra data.

A deterministic X-only scale floor `latest_amount*1e-12` keeps normalized
scores defined. Mack-normal baseline still uses the original raw standard
error. If Mack cannot fit a zero/nonfinite observed triangle, the declared
calibration score map uses zero reserve and latest-amount scale, with a visible
fallback flag. At test time the baseline fails, counting as uncovered;
calibrated methods return the entire real line, counted as unbounded, rather
than disguising a successful reserve fit. Invalid shapes, missing observed
cells, negative/nonfinite inputs or invalid exposure are pipeline errors.

Negative reserve targets/endpoints stay signed. No zero clipping, redraw,
failure deletion, repaired source value or selected favorable scenario is
allowed. Summaries report all cases, failures, unbounded intervals, finite
counts, coverage, Wilson Monte Carlo ranges, scaled widths and interval scores.
Any failure/unbounded interval makes the all-case width/score infinite; finite
means are explicitly conditional on finite intervals. Calibration-derived
exposure quartiles diagnose group coverage, without subgroup validity claims.
Wilson ranges concern independent synthetic test cases conditional on the
fixed calibration model, not real-world population or public-fold uncertainty.

## Verification and release

The protocol, implementation, tests, scorer and workflow are published before
any new primary draws. Development tests use hand-built toy data and the
already-inspected RAA oracle. Calibration models are persisted and hashed before
evaluation generation. All 6,144 observed triangles, seeds, realized targets
and feature records are retained, together with all 98,304 interval comparisons.
An independent scalar Mack implementation and separate rank/score calculator
check every forecast and interval. CI replays all **new** design draws; none of
the old 1,024 study seeds are rerun by this extension. Existing workflows may
perform their required historical regression checks with their original scope.

No client reserve/capital, IAS 19/ASC 715 valuation, external review, adoption,
independent candidate mastery or hiring outcome is claimed. Exactly seven
families; Stage One open, Stage Two deferred; applications/outreach on HOLD.
