"""Registered Mack-moment predictive sensitivity; not a coverage theorem.

Positive cumulative claims may fall between ages. Negative increments/reserves
are retained. Shared-factor simulation is an explicit moment approximation,
not a parametric bootstrap or a posterior. Dispersion estimates remain fixed.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import binom, norm
from src.stochastic_reserving import mack

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'reference/predictive_reserving'
PROBS = [.025, .1, .5, .9, .95, .975, .995]
SCENARIOS = ['independent_lognormal', 'independent_gamma',
             'future_calendar_shock', 'shared_calendar_lognormal']
METHODS = ['mack_normal', 'mack_lognormal', 'shared_lognormal', 'shared_gamma']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def protocol_guard():
    p = json.loads((STUDY / 'PROTOCOL.json').read_text())
    receipt = json.loads((STUDY / 'registration_receipt.json').read_text())
    if sha(STUDY / 'PROTOCOL.json') != receipt['protocol_sha256']:
        raise ValueError('Registered protocol changed')
    for path, digest in receipt['frozen_sha256'].items():
        if sha(ROOT / path) != digest:
            raise ValueError('Registered method changed: ' + path)
    for path, digest in p['original_source_sha256'].items():
        if sha(ROOT / path) != digest:
            raise ValueError('Historical source changed: ' + path)
    return p


def load_public(path, measure='values'):
    df = pd.read_csv(path)
    required = ['origin', 'development', measure]
    if any(k not in df for k in required) or df[required].isna().any().any():
        raise ValueError('Missing registered source fields')
    years = sorted(df.origin.unique())
    if len(years) < 4 or not np.array_equal(np.diff(years), np.ones(len(years)-1)):
        raise ValueError('Need consecutive annual origins')
    c = np.full((len(years), len(years)), np.nan)
    for row in df[required].itertuples(index=False, name=None):
        origin, calendar, value = row
        age = int(calendar-origin)
        if calendar-origin != age or not 0 <= age < len(years):
            raise ValueError('Invalid annual calendar age')
        i = years.index(origin)
        if np.isfinite(c[i, age]):
            raise ValueError('Duplicate source key')
        c[i, age] = float(value)
    mack(c)  # strict mask, positivity; negative increments are allowed
    return c, [int(y) for y in years]


def parts(c):
    fit = mack(c)
    n = len(c)
    fit['sums'] = np.array([c[:n-k-1, k].sum() for k in range(n-1)])
    return fit


def one_step_moments(x, factor, sigma_squared, fit_sum):
    if x <= 0 or factor <= 0 or sigma_squared < 0 or fit_sum <= 0:
        raise ValueError('Invalid one-step moments')
    return (x * factor, sigma_squared*x + sigma_squared/fit_sum*x*x)


def moment_quantiles(mean, variance, family):
    if not np.isfinite(mean+variance) or variance < 0:
        raise ValueError('Invalid moments')
    q = np.asarray(PROBS)
    if variance == 0:
        return np.full(len(q), mean)
    if family == 'normal':
        return mean + norm.ppf(q) * np.sqrt(variance)
    if family != 'lognormal' or mean <= 0:
        raise ValueError('Lognormal requires a positive mean')
    v = np.log1p(variance/mean**2)
    return np.exp(np.log(mean)-v/2 + np.sqrt(v)*norm.ppf(q))


def positive_draw(mean, variance, rng, family):
    mean, variance = np.broadcast_arrays(np.asarray(mean), np.asarray(variance))
    if (not np.all(np.isfinite(mean+variance)) or np.any(mean < 0) or
        np.any(variance < 0) or np.any((mean == 0)&(variance > 0))):
        raise ValueError('Nonnegative conditional moments required')
    out = mean.copy().astype(float)
    nz = variance > 0
    if family == 'lognormal':
        v = np.logaddexp(0, np.log(variance[nz])-2*np.log(mean[nz]))
        out[nz] = np.exp(np.log(mean[nz])-v/2 + np.sqrt(v)*rng.standard_normal(v.shape))
    elif family == 'gamma':
        out[nz] = rng.gamma(np.exp(2*np.log(mean[nz])-np.log(variance[nz])),
                            np.exp(np.log(variance[nz])-np.log(mean[nz])))
    else:
        raise ValueError('Unknown positive family')
    # Extreme small-shape gamma draws can underflow to exactly zero. Keep
    # those zeros and their absorbing 0/0-moment transitions; never floor,
    # redraw or discard a losing simulation. Counts are disclosed below.
    if not np.all(np.isfinite(out)) or np.any(out < 0):
        raise ValueError('Negative or nonfinite simulated cumulative amount')
    return out


def shared_projection(c, draws, seed, family, process_only=False):
    """Shared independent age factors plus conditionally independent origins.

    E[f*]=f, Var[f*]=sigma2/sum(C). The same factor draw is shared by all
    origins reaching that age. E[Cnext|C,f*]=f*C; Var= sigma2*C. No sigma
    re-estimation, empirical resampling, factor dependence or common calendar
    shocks are silently included. Exact conditional moments give a law-of-
    total-variance decomposition, distinct from Mack's first-order formula.
    """
    fit = parts(c)
    n = len(c)
    rng = np.random.default_rng(np.random.SeedSequence(seed))
    f, s, sums = fit['factors'], fit['sigma_squared'], fit['sums']
    factors = np.broadcast_to(f, (draws, n-1)).copy() if process_only else positive_draw(
        np.broadcast_to(f, (draws, n-1)), np.broadcast_to(s/sums, (draws, n-1)), rng, family)
    latest = fit['latest']
    amount = np.broadcast_to(latest, (draws, n)).copy()
    conditional_mean = amount.copy()
    conditional_variance = np.zeros_like(amount)
    for k in range(n-1):
        origins = np.flatnonzero(n-np.arange(n)-1 <= k)
        fstar = factors[:, k, None]
        before = conditional_mean[:, origins].copy()
        conditional_variance[:, origins] = (fstar**2*conditional_variance[:, origins] + s[k]*before)
        conditional_mean[:, origins] = fstar*before
        mean = fstar*amount[:, origins]
        variance = s[k]*amount[:, origins]
        amount[:, origins] = positive_draw(mean, variance, rng, family)
    reserve = amount.sum(axis=1)-latest.sum()
    parameter = conditional_mean.sum(axis=1)-latest.sum()
    process_variance = float(conditional_variance.sum(axis=1).mean())
    parameter_variance = float(parameter.var(ddof=1))
    return dict(reserve=reserve, parameter_reserve=parameter,
                expected_conditional_process_variance=process_variance,
                shared_parameter_variance=parameter_variance,
                total_mixture_variance=process_variance+parameter_variance,
                final_zero_origin_draws=int(np.sum(amount == 0)))


def order_bracket(values, probability):
    """Conservative binomial order-statistic MC bracket; not model coverage."""
    x = np.sort(np.asarray(values))
    n = len(x)
    lo = max(1, int(binom.ppf(.025, n, probability)))
    hi = min(n, int(binom.ppf(.975, n, probability))+1)
    return dict(lower_rank=lo, upper_rank=hi, lower=float(x[lo-1]), upper=float(x[hi-1]))


def sample_summary(values):
    values = np.asarray(values)
    return dict(mean=float(values.mean()), std=float(values.std(ddof=1)),
                min=float(values.min()), max=float(values.max()),
                nonpositive=int(np.sum(values <= 0)), draws=len(values),
                quantiles={str(p): float(q) for p,q in zip(PROBS,np.quantile(values,PROBS))},
                quantile_mc_brackets={str(p):order_bracket(values,p) for p in [.025,.975,.995]})


def interval_score(actual, lower, upper, alpha):
    if not 0 < alpha < 1 or lower > upper:
        raise ValueError('Invalid interval')
    return upper-lower + (2/alpha)*(max(lower-actual, 0)+max(actual-upper, 0))


def score_row(actual, q, scale):
    if scale <= 0 or not np.all(np.isfinite(q)) or np.any(np.diff(q) < 0):
        raise ValueError('Invalid scored predictive quantiles')
    return dict(q025=float(q[0]),q10=float(q[1]),median=float(q[2]),q90=float(q[3]),
                q95=float(q[4]),q975=float(q[5]),q995=float(q[6]),
                cover80=bool(q[1] <= actual <= q[3]),cover95=bool(q[0] <= actual <= q[5]),
                upper95_exceeded=bool(actual > q[4]),
                width80_scaled=float((q[3]-q[1])/scale),width95_scaled=float((q[5]-q[0])/scale),
                score80_scaled=float(interval_score(actual,q[1],q[3],.2)/scale),
                score95_scaled=float(interval_score(actual,q[0],q[5],.05)/scale))


def public_diagonals(c, years):
    """Four latest eligible pre-final valuations, without future-fit cells."""
    n = len(c)
    rows = []
    for m in range(max(4,n-4),n):
        observed = c[:m,:m].copy()
        observed[np.fromfunction(lambda i,j:i+j >= m,(m,m),dtype=int)] = np.nan
        fit = parts(observed)
        means, variances, actuals, lasts = [], [], [], []
        for i in range(2,m):  # at least two historical age-pair observations
            k = m-i-1
            x, actual = observed[i,k], c[i,k+1]
            mu, var = one_step_moments(x,fit['factors'][k],fit['sigma_squared'][k],fit['sums'][k])
            key = dict(valuation=years[0]+m-1,origin=years[i],age=k+1,fit_rows=m-k-1,
                       actual=float(actual),chain_ladder=float(mu),no_development=float(x),
                       process_variance=float(fit['sigma_squared'][k]*x),
                       parameter_variance=float(fit['sigma_squared'][k]/fit['sums'][k]*x*x),
                       training_array_sha256=hashlib.sha256(observed.tobytes()).hexdigest(),scope='cell')
            for family in ['normal','lognormal']:
                rows.append(dict(**key,method='mack_'+family,
                    **score_row(actual,moment_quantiles(mu,var,family),x)))
            means.append(mu);variances.append(var);actuals.append(actual);lasts.append(x)
        # Observed subset only; excludes new origin, last age with one pair.
        for family in ['normal','lognormal']:
            rows.append(dict(valuation=years[0]+m-1,origin=-1,age=-1,fit_rows=len(lasts),
                actual=float(sum(actuals)),chain_ladder=float(sum(means)),no_development=float(sum(lasts)),
                process_variance=None,parameter_variance=None,
                training_array_sha256=hashlib.sha256(observed.tobytes()).hexdigest(),scope='eligible_diagonal',
                method='mack_'+family,**score_row(sum(actuals),moment_quantiles(sum(means),sum(variances),family),sum(lasts))))
    return pd.DataFrame(rows)


def calendar_diagnostics(c, years):
    fit = parts(c)
    rows = []
    n = len(c)
    for k in range(n-2):
        x, z = c[:n-k-1,k], c[:n-k-1,k+1]
        if fit['sigma_squared'][k] <= 0:
            continue
        residual = (z-fit['factors'][k]*x)/np.sqrt(fit['sigma_squared'][k]*x)
        leverage = x/x.sum()
        residual = residual/np.sqrt(1-leverage)
        for i,r in enumerate(residual):
            rows.append(dict(calendar=years[i]+k+1,origin=years[i],age=k+1,residual=float(r)))
    return pd.DataFrame(rows)


def complete_simulation(case, seed):
    n = 8
    f = np.array([1.8,1.45,1.25,1.12,1.06,1.025,1.01])
    s = np.array([600.,240.,100.,40.,16.,6.4,2.56])
    full = np.empty((n,n))
    full[:,0] = 900.+180*np.arange(n)
    rng = np.random.default_rng(np.random.SeedSequence(seed))
    z = rng.standard_normal((n,n-1))
    calendar_z = rng.standard_normal(2*n-1)
    rho = .35 if case == 'shared_calendar_lognormal' else 0.
    if case not in SCENARIOS:
        raise ValueError('Unknown registered scenario')
    for i in range(n):
        for k in range(n-1):
            x = full[i,k]
            factor = f[k]*(1.10 if case == 'future_calendar_shock' and i+k+1 == n else 1.)
            mu, var = factor*x,s[k]*x
            if case == 'independent_gamma':
                cell_rng = np.random.default_rng(np.random.SeedSequence(list(seed)+[i,k,901]))
                full[i,k+1] = cell_rng.gamma(mu*mu/var,var/mu)
            else:
                v = np.log1p(var/mu**2)
                innovation = np.sqrt(1-rho)*z[i,k]+np.sqrt(rho)*calendar_z[i+k+1]
                full[i,k+1] = np.exp(np.log(mu)-v/2+np.sqrt(v)*innovation)
    observed = full.copy()
    observed[np.fromfunction(lambda i,j:i+j >= n,(n,n),dtype=int)] = np.nan
    latest = np.array([full[i,n-i-1] for i in range(n)])
    truth = float(full[:,-1].sum()-latest.sum())
    return observed,truth


def calibration_case(scenario_index, replicate, draws):
    case = SCENARIOS[scenario_index]
    observed,truth = complete_simulation(case,[20261011,scenario_index,replicate,0])
    fit = parts(observed)
    point = float(fit['ibnr'].sum())
    variance = fit['total_std_error']**2
    scale = float(fit['latest'].sum())
    rows = []
    for method in METHODS:
        key = dict(scenario=case,replicate=replicate,method=method,actual=truth,
                   point=point,scale=scale,training_array_sha256=hashlib.sha256(observed.tobytes()).hexdigest())
        try:
            if method.startswith('mack_'):
                q = moment_quantiles(point,variance,method.split('_',1)[1])
            else:
                family = method.split('_',1)[1]
                d = shared_projection(observed,draws,[20261011,scenario_index,replicate,1 if family=='lognormal' else 2],family)
                q = np.quantile(d['reserve'],PROBS)
            key['final_zero_origin_draws'] = d['final_zero_origin_draws'] if method.startswith('shared_') else 0
            rows.append(dict(**key,status='ok',error='',**score_row(truth,q,scale)))
        except (ValueError,FloatingPointError) as e:
            rows.append(dict(**key,status='failed',error=str(e)))
    return rows


def wilson(successes, n):
    if n <= 0:
        return [None,None]
    z = norm.ppf(.975); phat = successes/n
    a = (phat+z*z/(2*n))/(1+z*z/n)
    b = z*np.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(a-b),float(a+b)]


def calibration_summary(df):
    result = []
    for (case,method),g in df.groupby(['scenario','method'],sort=True):
        good = g[g.status=='ok']
        r = dict(scenario=case,method=method,cases=len(g),failed=len(g)-len(good))
        for level in [80,95]:
            count = sum(str(v).lower()=='true' for v in good['cover'+str(level)])
            r['covered'+str(level)] = count
            # Failed methods count as uncovered; they remain in denominator.
            r['coverage'+str(level)] = count/len(g)
            r['wilson'+str(level)] = wilson(count,len(g))
            r['mean_score'+str(level)+'_scaled'] = float(good['score'+str(level)+'_scaled'].mean()) if len(good) else None
            r['mean_width'+str(level)+'_scaled'] = float(good['width'+str(level)+'_scaled'].mean()) if len(good) else None
        r['upper95_exceeded'] = sum(str(v).lower()=='true' for v in good.upper95_exceeded)
        r['final_zero_origin_draws'] = int(good.final_zero_origin_draws.sum()) if 'final_zero_origin_draws' in good else 0
        r['score_denominator'] = len(good)
        r['scores_exclude_failures_but_failure_count_is_explicit'] = True
        result.append(r)
    return result
