"""Independent Mack (1993) implementation and historical diagonal backtests.

RAA is a published reinsurance benchmark, not health-insurance client data.
No tail beyond the final observed development age is assumed here.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_raa(path=None):
    frame = pd.read_csv(path or ROOT / 'data/raa.csv')
    years = sorted(frame.origin.unique())
    triangle = np.full((len(years), len(years)), np.nan)
    for r in frame.itertuples():
        triangle[years.index(r.origin), int(r.development-r.origin)] = r.values
    return triangle, years


def mack(triangle):
    c = np.asarray(triangle, dtype=float)
    n = len(c)
    if c.shape != (n, n) or n < 4:
        raise ValueError('Expected a square upper development triangle of size >=4')
    expected = np.fromfunction(lambda i, j: i+j < n, c.shape, dtype=int)
    if not np.array_equal(np.isfinite(c), expected) or np.any(c[expected] <= 0):
        raise ValueError('Require positive observed cells and a complete triangular mask')
    f, sigma2, sums = [], [], []
    for k in range(n-1):
        x, z = c[:n-k-1, k], c[:n-k-1, k+1]
        factor = z.sum()/x.sum()
        f.append(factor)
        sums.append(x.sum())
        sigma2.append(np.sum(x*(z/x-factor)**2)/(len(x)-1) if len(x)>1 else np.nan)
    f, sigma2, sums = map(np.asarray, (f, sigma2, sums))
    # Mack's conservative last-age extrapolation, not log-linear extrapolation.
    sigma2[-1] = min(sigma2[-2]**2/sigma2[-3], sigma2[-2], sigma2[-3]) if sigma2[-3] > 0 else 0.0
    full = c.copy()
    latest = np.asarray([c[i, n-i-1] for i in range(n)])
    for i in range(1, n):
        for k in range(n-i-1, n-1):
            full[i, k+1] = full[i, k]*f[k]
    ultimate = full[:, -1]
    process = np.zeros(n)
    parameter = np.zeros(n)
    for i in range(1, n):
        k = np.arange(n-i-1, n-1)
        process[i] = ultimate[i]**2*np.sum(sigma2[k]/f[k]**2/full[i, k])
        parameter[i] = ultimate[i]**2*np.sum(sigma2[k]/f[k]**2/sums[k])
    covariance = 0.0
    for i in range(1, n):
        for j in range(i+1, n):
            k = np.arange(max(n-i-1, n-j-1), n-1)
            covariance += 2*ultimate[i]*ultimate[j]*np.sum(sigma2[k]/f[k]**2/sums[k])
    return dict(factors=f, sigma_squared=sigma2, latest=latest, ultimate=ultimate,
                ibnr=ultimate-latest, process_variance=process,
                parameter_variance=parameter, origin_std_error=np.sqrt(process+parameter),
                total_std_error=float(np.sqrt(process.sum()+parameter.sum()+covariance)),
                aggregate_parameter_covariance=float(covariance))


def diagonal_backtest(c, years):
    rows = []
    for cutoff in range(1986, 1990):
        observed = c.copy()
        for i, year in enumerate(years):
            for age in range(len(years)):
                if year+age > cutoff:
                    observed[i, age] = np.nan
        for i, year in enumerate(years):
            age = cutoff-year
            if not 0 <= age < len(years)-1 or not np.isfinite(c[i, age+1]):
                continue
            usable = np.isfinite(observed[:, age]) & np.isfinite(observed[:, age+1])
            if usable.sum() < 2 or not np.isfinite(observed[i, age]):
                continue
            x, z = observed[usable, age], observed[usable, age+1]
            factor = z.sum()/x.sum()
            rows.append(dict(valuation_year=cutoff, origin=year, development_age=age+1,
                             factor_fit_rows=int(usable.sum()), actual_next=c[i, age+1],
                             chain_ladder_next=observed[i, age]*factor,
                             no_development_next=observed[i, age]))
    return pd.DataFrame(rows)


def main():
    c, years = load_raa()
    fit = mack(c)
    out = ROOT/'outputs/stochastic_reserving'
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(dict(origin=years, latest=fit['latest'], ultimate=fit['ultimate'],
                      ibnr=fit['ibnr'], mack_std_error=fit['origin_std_error'])).to_csv(out/'raa_reserves.csv', index=False)
    pd.DataFrame(dict(development_age=np.arange(1, len(years)), factor=fit['factors'],
                      sigma_squared=fit['sigma_squared'])).to_csv(out/'development_factors.csv', index=False)
    bt = diagonal_backtest(c, years)
    bt.to_csv(out/'diagonal_backtest.csv', index=False)
    summary = dict(dataset='Published RAA reinsurance triangle, 1981-1990',
                   data_sha256=hashlib.sha256((ROOT/'data/raa.csv').read_bytes()).hexdigest(),
                   observed_cells=int(np.isfinite(c).sum()), total_ibnr=float(fit['ibnr'].sum()),
                   total_mack_std_error=fit['total_std_error'],
                   std_error_over_reserve=fit['total_std_error']/float(fit['ibnr'].sum()),
                   backtest_cells=len(bt),
                   next_diagonal_chain_ladder_mae=float(abs(bt.chain_ladder_next-bt.actual_next).mean()),
                   next_diagonal_no_development_mae=float(abs(bt.no_development_next-bt.actual_next).mean()),
                   tail_factor=1.0, unit='original published triangle units; no currency relabelling',
                   caveat='Retrospective benchmark replication; standard error is not a quantile or calibrated capital margin.')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
