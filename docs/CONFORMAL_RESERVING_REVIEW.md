# Whole-triangle calibration and transfer challenge

**Registered:** 2026-10-12, before all new calibration/evaluation draws; commit `73bf40e2fa16cb7bd81fabc04c320abfa87cff2a`. [Protocol](../reference/conformal_reserving/PROTOCOL.json) · [Design and assumptions](CONFORMAL_RESERVING_DESIGN.md) · [All 96 result groups](../outputs/conformal_reserving/SUMMARY.json) · [Exposure diagnostics](../outputs/conformal_reserving/exposure_strata.json)

## Result and its limits

Calibration improves the matched-law predictive intervals in these four fixed synthetic laws. It does not repair distribution shift or establish real-insurer calibration. Absolute conformal nominal-95% coverage is 95.12–95.90% with matched calibration, but only 83.98% when an independent-lognormal calibrator is transferred to shared-calendar triangles. The scaled alternative is not uniformly better: it is wider and has worse interval scores than calibrated normal in all four matched-law 95% groups. All methods, levels, widths, scores and adverse strata remain reported.

## Locked comparison

Each of four previously inspected synthetic laws has 512 new independent whole calibration triangles and 1,024 separate new whole evaluation triangles: 2,048 calibration + 4,096 evaluation = 6,144 distinct draws. Seed root 20261012, namespace 73991, role 1/2 separates calibration/evaluation. The 98,304 interval rows reuse the same 4,096 test cases across two calibration modes, four methods and three levels; they are not additional independent trials. Original six public benchmark measures, 123 later-diagonal cells, 22 inspected RAA predictions and prior 1,024-case simulation are unchanged.

Raw Mack normal uses no calibration outcomes; the other three methods each receive the same 512 labelled calibration cases per calibration law. Calibrated normal estimates signed normalized residual mean and sample standard deviation. Absolute conformal ranks absolute errors; scaled conformal ranks errors divided by an X-only Mack scale. This extra information budget is explicit, so the comparison is not equal-information superiority over Mack. All calibration models were persisted and SHA256-hashed before any evaluation generation: `c27c0250b634a3fe0f8a6c055fb68837cbe2f42bc086c81d1d14a63189bd757b`.

Four laws: independent lognormal, independent gamma, a 10% mean shock at the first unobserved calendar, and lognormal innovations with shared-calendar correlation rho=0.35. Matched calibration includes the same shock or dependence law in calibration and testing. It therefore has information about the fixed shifted law; it is not adaptation to an unforeseen new regime.

## Nominal-95% coverage

Each cell below is covered/1,024 (percentage). The underlying SUMMARY includes Wilson 95% Monte Carlo intervals. These quantify independent test-draw uncertainty conditional on the frozen calibrator, not uncertainty across calibration sets or client populations.

### Matched law

| Evaluation law | Raw Mack | Calibrated normal | Absolute conformal | Scaled conformal |
|---|---:|---:|---:|---:|
| Independent lognormal | 957/1024 (93.46%) | 986/1024 (96.29%) | 982/1024 (95.90%) | 996/1024 (97.27%) |
| Independent gamma | 961/1024 (93.85%) | 977/1024 (95.41%) | 976/1024 (95.31%) | 972/1024 (94.92%) |
| Future calendar shock | 833/1024 (81.35%) | 972/1024 (94.92%) | 974/1024 (95.12%) | 981/1024 (95.80%) |
| Shared calendar lognormal | 818/1024 (79.88%) | 960/1024 (93.75%) | 977/1024 (95.41%) | 972/1024 (94.92%) |

### Unchanged independent-lognormal calibrator transferred to each law

| Evaluation law | Raw Mack | Calibrated normal | Absolute conformal | Scaled conformal |
|---|---:|---:|---:|---:|
| Independent lognormal | 957/1024 (93.46%) | 986/1024 (96.29%) | 982/1024 (95.90%) | 996/1024 (97.27%) |
| Independent gamma | 961/1024 (93.85%) | 989/1024 (96.58%) | 982/1024 (95.90%) | 996/1024 (97.27%) |
| Future calendar shock | 833/1024 (81.35%) | 908/1024 (88.67%) | 910/1024 (88.87%) | 921/1024 (89.94%) |
| Shared calendar lognormal | 818/1024 (79.88%) | 874/1024 (85.35%) | 860/1024 (83.98%) | 917/1024 (89.55%) |

The independent-lognormal row has the same calibrator in both modes and is intentionally duplicated for comparison, not new evidence. At shared-calendar transfer, absolute conformal is 860/1,024, Wilson interval 81.61–86.10%; scaled conformal is 917/1,024, interval 87.53–91.28%. Both remain well below nominal 95%.

## Width and interval score at 95%, matched law

Values are means of width and proper interval score divided by latest observed cumulative exposure. Lower interval score is better; narrower width alone does not show calibration. All 1,024 intervals in every group are finite in this run, so conditional and all-case means coincide.

| Law | Raw Mack width / score | Calibrated normal width / score | Absolute conformal width / score | Scaled conformal width / score |
|---|---:|---:|---:|---:|
| Independent lognormal | 0.6101 / 0.8317 | 0.7089 / 0.8143 | 0.6704 / 0.7707 | 0.7912 / 0.8764 |
| Independent gamma | 0.6247 / 0.8870 | 0.6847 / 0.8764 | 0.6484 / 0.7991 | 0.6717 / 0.8878 |
| Future calendar shock | 0.6065 / 1.4839 | 0.7149 / 0.8966 | 0.8093 / 0.9748 | 1.0253 / 1.1827 |
| Shared calendar lognormal | 0.6099 / 1.6646 | 0.9530 / 1.2892 | 0.9605 / 1.1384 | 1.0390 / 1.3289 |

Absolute conformal has the best recorded matched-law interval score for the two independent laws and shared-calendar law. Calibrated normal has the best score for the future-calendar shock (0.8966 versus absolute 0.9748 and scaled 1.1827). This is a descriptive result for this fixed split, not a method selected after evaluation or a universal ranking.

## Lower levels and subgroup diagnostics

At matched-law nominal 80%, absolute conformal coverage ranges 77.25–82.52%; at 90%, 86.91–91.60%. Scaled conformal ranges 78.22–82.03% and 88.48–91.89% respectively. A marginal finite-sample rank guarantee does not force every realized frozen-calibrator test batch above its target.

Exposure quartiles were set using matched-scenario calibration X values only. At shared-calendar 95%, absolute conformal covers 251/279 (89.96%) in the highest-exposure quartile; scaled conformal covers 220/255 (86.27%) in the lowest-exposure quartile. These are diagnostic strata with no group-coverage guarantee or multiplicity-adjusted inference. The complete 384 strata are retained.

## Failure handling and audit

Zero calibration failures, zero evaluation failures and zero scale-floor cases occurred; there were no redrawn or omitted cases. The registered code still treats failed Mack evaluation fits as failed/uncovered for raw Mack and unbounded whole-real-line intervals for calibrated methods. Such cases force infinite all-case mean width/score rather than disappear from denominators. Signed reserve outcomes and negative endpoints are retained; no zero clipping.

The independent checker imports neither the new interval implementation nor the runner. It reconstructs all 6,144 Mack forecasts using scalar loops, checks calibration order statistics/mean/std, checks all 98,304 interval endpoints/statuses/coverage/width/scores, all summary counts and 384 exposure strata, and replays all 6,144 new synthetic targets from the unchanged generator. It reruns no prior 1,024-study seeds. [Audit receipt](../reference/conformal_reserving/INDEPENDENT_AUDIT.json). This is internal automated verification, not independent practitioner review. The registered checker re-decompresses whole NPZ arrays on each loop index. A documented post-study [execution-only amendment](../reference/conformal_reserving/COMPUTATIONAL_AMENDMENT.json) loads each array once in memory and calls the same unchanged checker. CI changes only that invocation; no mathematical source, tolerance, case, seed, output or protocol changed. The original registered workflow/hash remains in the registration commit and receipt.

## Interpretation and references

The finite-sample conformal statement is marginal over exchangeable calibration/test pairs, not conditional on this realized calibration set, cellwise independence, a future temporal regime, exposure groups, solvency capital or a real insurer. Whole triangles are the independent units here. Transfer to a different law has no such guarantee. Additional shift-aware methods or group methods would require a separately registered design; these outcomes were not used to change the completed protocol.

Primary methodological references: [Angelopoulos and Bates, A Gentle Introduction to Conformal Prediction](https://arxiv.org/abs/2107.07511), rank construction and normalized regression scores; [Lei et al., Distribution-Free Predictive Inference for Regression](https://www.stat.cmu.edu/~ryantibs/papers/conformal.pdf), split conformal regression. This project implements and tests known methods; it introduces no original coverage theorem.

## Verify without generating a new study

```bash
python -m pip install -r requirements-predictive.txt
python -m pytest -q
python audit_conformal_cached.py
```

`benchmark_conformal_reserving.py` refuses to overwrite an existing output directory. Reproduction of new study draws requires a separate empty checkout/output location; do not delete published evidence or rerun old studies to manufacture a new result. The new workflow performs the independent saved-result/new-design replay and all tests; the two existing workflows keep their established regression scope. No new model inference, public/client outcomes, adoption, external review or Stage Two mastery is claimed.
