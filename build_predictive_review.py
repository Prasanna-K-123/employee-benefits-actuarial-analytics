"""Build the reviewer memo from the frozen study tables, without refitting."""
from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'outputs/predictive_reserving'
S=json.loads((OUT/'summary.json').read_text())
P=json.loads((ROOT/'reference/predictive_reserving/PROTOCOL.json').read_text())
R=json.loads((ROOT/'reference/predictive_reserving/registration_receipt.json').read_text())
C=json.loads((OUT/'calibration_summary.json').read_text())
U=json.loads((OUT/'public_reserve_summary.json').read_text())
D=pd.read_csv(OUT/'public_diagonal_summary.csv')

public='| Measure | Cells | CL MAE | No-development MAE | Normal 95% covered | Lognormal 95% covered |\n|---|---:|---:|---:|---:|---:|\n'
for name in U:
 a=D[(D.dataset==name)&(D.scope=='cell')&(D.method=='mack_normal')].iloc[0]
 b=D[(D.dataset==name)&(D.scope=='cell')&(D.method=='mack_lognormal')].iloc[0]
 public+=f'| {name} | {a.observations} | {a.chain_ladder_mae:,.2f} | {a.no_development_mae:,.2f} | {a.covered95}/{a.observations} | {b.covered95}/{b.observations} |\n'
cal='| Simulation design | Method | 80% covered / 256 | 95% covered / 256 | 95% coverage | Wilson MC bracket | Failed | Mean 95% interval score / latest |\n|---|---|---:|---:|---:|---:|---:|---:|\n'
for x in C:
 lo,hi=x['wilson95']
 cal+=f"| {x['scenario']} | {x['method']} | {x['covered80']} | {x['covered95']} | {100*x['coverage95']:.1f}% | {100*lo:.1f}-{100*hi:.1f}% | {x['failed']} | {x['mean_score95_scaled']:.4f} |\n"
quant='| RAA reserve approximation | 2.5th | Median | 97.5th | 99.5th |\n|---|---:|---:|---:|---:|\n'
for mode in ['mack_normal','mack_lognormal','lognormal_combined','gamma_combined']:
 q=U['raa']['modes'][mode]['quantiles']
 quant+=f"| {mode} | {q['0.025']:,.2f} | {q['0.5']:,.2f} | {q['0.975']:,.2f} | {q['0.995']:,.2f} |\n"

text=f'''# Predictive reserving: uncertainty and calibration review

Independent AI-assisted portfolio research. Completed 2026-10-11. All amounts retain each published benchmark's units. This is not client claims data, a professional actuarial opinion or regulatory capital calibration.

## Decision finding

The original RAA replication remains correct: **55 observed cells**, IBNR **52,135.23**, aggregate Mack standard error **26,909.01**, nine external rounded origin standard-error references and the same **22 inspected later-diagonal forecasts**. Reproducing a standard error does not establish an entire predictive distribution or its calibration.

This registered extension compares six cumulative benchmark measures from five files, **123 eligible later-diagonal cells** and **23 eligible diagonal sums**. Point forecasts beat no-development MAE on all six measures, while nominal 95% moment intervals cover only **8/26 ABC cells**, **12/22 USAA incurred cells**, and **0/4 USAA paid eligible diagonal sums**. These are dependent retrospective diagnostics, not estimates of population coverage or observations of final reserve truth.

The controlled study executes all **1,024 fixed cases** across four data-generating designs. Four methods produce **4,092 scored rows** and **four retained failures** from one numerically degenerate gamma training case. Nominal 95% aggregate reserve intervals achieve only **79.3-83.6%** coverage with shared calendar innovations and **82.0-87.5%** under a future calendar shock. Stable independent designs also show imperfect finite-sample coverage. No method is declared calibrated or chosen as a winner after seeing the outcomes.

![Coverage and assumption stress](../outputs/predictive_reserving/predictive_coverage.png)

## Registration and immutable history

- Initial public source/design registration **{R['initial_registration_commit']}**, protocol SHA256 `{R['initial_protocol_sha256']}`, precedes collection of four new exact CSV blobs and primary execution. RAA and documentation examples, including some ABC summaries, were already inspected; no public benchmark is claimed as an untouched prospective holdout.
- Dependency integration amendment **{R['pre_execution_dependency_commit']}** adds SciPy to the original requirements before the primary run. Initial historical CI failed solely because new predictive tests imported absent SciPy; the failure is retained in the protocol, not presented as a successful run.
- Computational amendment **{R['commit']}**, protocol SHA256 `{S['protocol_sha256']}`, records the interrupted run's gamma numerical-zero handling and full-method failure recording. The first attempt emitted 320 case completions, then stopped; it produced no durable calibration case table. Seven completed public files remain byte-identical. No data, statistical family, factor/variance specification, seed, draw budget, score or case menu was changed based on results.
- All 28 original files remain present. **25 original blobs** are unchanged; README/evidence-review prose is extended and the original dependency file gains pinned SciPy. Historical source, 12 original tests, RAA outputs, synthetic benefits data and published workbook bytes remain unchanged. No old benchmark table is regenerated over its published bytes.

## Data lineage and eligibility

The source registry and blobs are pinned to `casact/chainladder-python` commit **{P['upstream_commit']}**. The unmodified `genins.csv`, `abc.csv`, `ukmotor.csv` and `usaa.csv` blobs are verified by Git blob SHA1, byte length and recorded SHA256. Original `data/raa.csv` keeps its previous bytes and attribution. The source receipt retains the initial collection registration; later code amendments do not rewrite that collection history. MPL-2.0 and a source notice accompany redistributed samples.

RAA: 10 origins/55 cells; GenIns: 10/55; ABC: 11/66; UK motor: 7/28; USAA paid and incurred: 10/55 each. There are **six measures**, not six independent insurers: USAA paid and incurred share a source. No currency, employer/client identity or release-feasible historical access is invented. Convenience sample selection and old public availability limit generalization.

Every observed cumulative cell must be finite and positive with a complete annual triangular mask. Negative incremental development is retained: one negative RAA increment and **43** USAA incurred increments. USAA incurred's total projected reserve is **-755,258.40**, interpreted as negative development on an incurred benchmark, not negative future paid cash claims or a booked liability. Its positive-reserve lognormal approximation is explicitly unavailable; normal and cumulative-process simulations retain negative reserve outcomes.

## Methods and assumptions

For age k, ordinary volume-weighted chain ladder estimates `f = sum(Cnext)/sum(C)` and `sigma2 = sum(C*(Cnext/C-f)^2)/(pairs-1)`. The one-pair final age uses the existing conservative Mack extrapolation. Shared parameter covariance across origin reserves is retained in the original analytic aggregate standard error. Official implementations can instead use log-linear last-age extrapolation; their default aggregate error need not match this explicitly stated choice.

**One-step prediction:** for latest amount x, mean `x*f`, process variance `sigma2*x`, and estimated-factor variance `x*x*sigma2/sum(C)`. Normal and lognormal moment approximations share those two moments. The lognormal is applied to the next **positive cumulative amount**, allowing an implied negative increment. Central 80/95% intervals, upper 95% exceedances, widths and interval scores are reported. No endpoint is clipped to latest paid claims or zero.

**Full-reserve analytic approximation:** apply normal or, when mean reserve is positive, lognormal moments to aggregate reserve using the original Mack standard error. This is a shape assumption, not a distribution-free quantile theorem or a posterior. The normal RAA lower 2.5th percentile is negative and remains visible.

**Shared-factor moment simulation:** draw positive independent age factors with `E[f*]=f` and `Var[f*]=sigma2/sum(C)`. Each drawn age factor is shared by every origin reaching that age. Conditional gamma or lognormal cumulative transitions have `E[Cnext|C,f*]=f*C` and `Var[Cnext|C,f*]=sigma2*C`. All fitted sigma2 values remain fixed. This is **not** residual resampling, a parametric bootstrap, parameter posterior or proof that factor-estimation error has that distribution. It excludes dispersion-estimation and cross-age factor dependence. Those omissions help explain why it must be calibrated empirically before any stronger use.

Each public family uses **8,192 draws**. Parameter-only values are conditional expected reserves from the same factor draws; process-only projections hold fitted factors fixed and use separately seeded innovations. They are distinct uncertainty components, not separate independent studies or an additive decomposition obtained by subtracting noisy sample variances. For each factor draw, recursively compute conditional means and variances; `E[Var(reserve|f*)] + Var(E[reserve|f*])` supplies the law-of-total-variance decomposition. Its higher-order moment mixture need not equal Mack's analytic first-order formula.

Small-shape gamma draws may underflow to exactly zero in floating point. Such states are kept and become absorbing, with no floor, redraw or dropped trajectory. RAA combined gamma has **1,430 final zero-origin states** across 8,192 x 10 origin outcomes; process-only has **742**. These are origin-state counts, not 1,430 failed simulations or negative client claims. This numerical approximation is disclosed; lognormal RAA has none. Public quantile MC brackets use conservative binomial order ranks and assess simulation precision only. Even 8,192 draws do not validate a 99.5% capital quantile.

## Historical later-diagonal evaluation

For n origins, use valuation sizes `m=max(4,n-4),...,n-1`. Fit only the m x m observed upper triangle, `i+j<m`; use eligible origins `i=2,...,m-1`, so every forecast age has at least two historical age-pair observations. Predict the next known cumulative cell. Evaluation outcomes never fit factors or sigmas. Mutating a last-diagonal outcome leaves earlier forecasts/intervals unchanged in an independent test.

The aggregate target sums **only eligible cells**; it excludes a newly appearing origin and the oldest eligible age with only one fitted pair. It is not a full claims-development-result calculation. Every cell's fitted pair count, variance components and training-array hash are saved. The same 22 RAA predictions reconcile to the previously published rows; no fresh holdout label is attached.

{public}

MAE amounts are meaningful only within the same benchmark units. Coverage counts share triangle/fold dependence; no naive binomial population confidence interval, pooled cross-currency loss or industry-wide claim is made. The full table also reports 80% coverage, proper interval scores and eligible-diagonal results, including all failures of apparently precise forecasts.

## Controlled calibration with known realized future claims

Generate full 8-origin cumulative paths and reveal 36 observed triangular cells. First amounts are `[900,1080,1260,1440,1620,1800,1980,2160]`; age factors `[1.8,1.45,1.25,1.12,1.06,1.025,1.01]`; sigma2 `[600,240,100,40,16,6.4,2.56]`. The last true sigma2 agrees with the fixed geometric Mack extrapolation at the population values; finite-sample estimates still vary.

The actual target is realized full-horizon aggregate ultimate minus latest observed sum, including negative realized reserves where they occur. It is not the known mean reserve. Each design has **256 independently seeded cases**:

1. Independent positive lognormal cumulative transitions, matching the stated conditional moments.
2. Independent gamma transitions with the same moments. Case **69** has two observed numerical-zero cells; all four methods refuse invalid positive training and are counted uncovered. The true future is retained using the declared absorbing-zero rule.
3. Independent lognormal paths with a **10% mean-factor shock on the first unobserved calendar only**; variance remains `sigma2*C`, later factors stable. This unobservable shock challenges extrapolation; no fitted calendar model is implied.
4. Lognormal paths with shared same-calendar normal innovations, **rho=0.35**. Conditional cell means/variances remain specified while origin independence is violated. This is a stress design, not an estimated real insurer correlation.

Forecasts use only the observed triangle and **4,096 draws per shared-factor method per valid case**. All four methods share each case's outcomes. Seed IDs and budgets are frozen; Wilson brackets describe Monte Carlo uncertainty over independent **simulated cases**, not real-insurer coverage, a method-selection p-value or an asymptotic theorem. Failures remain in the coverage denominator; scores exclude them with their count/denominator explicit.

{cal}

These results do not support universal nominal coverage, including under independent designs. None of the methods is tuned or chosen from this comparison. No learned calendar coefficient or wider corrective interval is promoted on these already inspected evaluation cases.

## Tail and calendar sensitivity

{quant}

These RAA values are model-implied/empirical approximation quantiles, not observed final-reserve quantiles. Family and parameter-risk representation change their tails even while matching local first two moments. Full raw draw arrays and order-statistic MC brackets are retained.

Deterministic tail factors **1.00/1.01/1.025/1.05** multiply all final-age ultimate values, including the oldest origin. RAA's 2.5% tail assumption adds **5,328.06** reserve units. The existing standard error is multiplied by the tail factor with **no added tail-estimation/process variance**; it must not be described as full uncertainty after tail modelling. No tail factor is selected as best.

Leverage-adjusted Mack residuals are tabulated by calendar and age with counts, means and standard deviations. These are descriptive diagnostics. No approximate calendar test is substituted for a validated dependence model, and a small residual pattern cannot prove stable future calendar behaviour.

## Alternatives and primary references

- [Mack (1993)](https://www.cambridge.org/core/journals/astin-bulletin-journal-of-the-iaa/article/distributionfree-calculation-of-the-standard-error-of-chain-ladder-reserve-estimates/E8D207F9A4DCE30300A76780FE510437) motivates conditional first/second moments and independent origins; [official Mack implementation](https://mages.github.io/ChainLadder/reference/MackChainLadder.html) states those assumptions and last-age/tail options.
- [Steinmetz and Jentsch (2023)](https://arxiv.org/abs/2303.05913) separates process/estimation bootstrap behaviour and the importance of parametric-family assumptions. The present heuristic does not claim to implement their alternative consistency result.
- [Official England/Verrall-style bootstrap implementation](https://mages.github.io/ChainLadder/reference/BootChainLadder.html) resamples scaled incremental residuals and separately simulates process uncertainty. That different ODP model needs explicit signed-increment handling; it is not silently relabelled as Mack or declared universally invalid on negative increments.
- [Official Cornish-Fisher quantiles](https://mages.github.io/ChainLadder/reference/quantile.MackChainLadder.html) use additional skewness estimation. Higher-moment, residual-bootstrap and explicit Bayesian/calendar alternatives remain meaningful next comparisons, not claims reproduced here.

The finite menu makes this comparison reproducible; it does not prove a globally optimal method. A defensible next step is to register a distinct development/confirmation design for dispersion and calendar-aware methods, with original-vintage insurer/exposure data and credible tail information. Benefits mortality/turnover and real plan rules remain separate gaps; synthetic workbook mechanics do not become qualified pension/health valuations through this reserving study.

## Reproduction and verification

```bash
python -m pip install -r requirements-predictive.txt
python -m pytest -q
python collect_predictive_sources.py --verify-committed
python verify_predictive_reserving.py
```

**37 tests** retain all 12 historical tests and add independent predictive checks: hand-counted one-step moments, conditional distribution moments, loss-preserving scores, negative normal endpoints/increments, failure denominator, future-fit isolation, fixed eligible counts, future-shock separation, deterministic seeds, zero-state retention and scale equivalence.

The strict verifier checks **27 core manifest files**, all public projections/draw arrays/scores, original RAA rows, every one of the **1,024 generated designs and realized targets**, all stored method scores and the complete calibration summary. It reexecutes **16 fixed cases**: IDs 0/85/170/255 in each of four designs. The original study executed all 1,024; CI refits 16, not all 1,024. Numerical replay uses rtol 2e-10 / atol 2e-8; differing training-byte hashes are separately counted, without a universal bit-identical hardware claim.

For a new full execution, use an empty output directory inside this repository:

```bash
python benchmark_predictive_reserving.py --output outputs/predictive_reproduction --workers 4
```

Completed study output cannot be overwritten. Resume is restricted to the exact seven public files of an interrupted calibration; final summaries block resume. Source/hash changes block execution with no alternative mirror or silent source substitution. Recreating the coverage figure needs optional `matplotlib==3.10.8`, then `python plot_predictive_reserving.py`; it reads completed tables and never refits.

The [predictive workflow](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/predictive-reserving.yml) runs all tests and full registered replay on releases containing final results. Registration-only runs explicitly skip data replay before artifacts exist and are not cited as final study evidence. The unchanged [benefits workflow](https://github.com/Prasanna-K-123/employee-benefits-actuarial-analytics/actions/workflows/employee-benefits-actuarial-ci.yml) separately rebuilds/recalculates the Excel workbook and verifies historical Mack output. Exact successful release revisions/runs are linked from the current profile evidence guide after publication verification.
'''
(ROOT/'docs/PREDICTIVE_UNCERTAINTY_REVIEW.md').write_text(text)
print('Review bytes',len(text.encode()))
