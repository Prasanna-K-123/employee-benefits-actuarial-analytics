"""Whole-triangle split calibration, with explicit failure and shift limits.

The score map uses only an observed triangle and its realized reserve. Fitted
thresholds never receive an evaluation outcome. Coverage is marginal under
exchangeability of whole triangles; neither cells nor public temporal folds
are treated as independent calibration observations.
"""
from dataclasses import dataclass
from fractions import Fraction
import math
import numpy as np
from scipy.stats import norm
from src.stochastic_reserving import mack

METHODS = ('mack_normal', 'calibrated_normal', 'conformal_absolute', 'conformal_scaled')
LEVELS = (80, 90, 95)

@dataclass(frozen=True)
class Forecast:
    point: float
    scale: float
    exposure: float
    status: str
    raw_std_error: float | None = None

    def __post_init__(self):
        if (not all(math.isfinite(x) for x in (self.point,self.scale,self.exposure))
                or self.scale<=0 or self.exposure<=0
                or self.status not in ('ok','scale_floor','fallback_failed_mack')
                or (self.raw_std_error is not None and
                    (not math.isfinite(self.raw_std_error) or self.raw_std_error<0))):
            raise ValueError('Invalid forecast or undeclared failure status')

def forecast(observed):
    """No future cell/outcome argument is accepted.

    Failed Mack fits use a declared X-only zero-reserve/exposure-scale score
    map for calibration. Their baseline interval is still failed; calibrated
    methods return the whole real line at prediction, never a hidden success.
    """
    c = np.asarray(observed, dtype=float)
    if c.ndim != 2 or c.shape[0] != c.shape[1] or len(c) < 4:
        raise ValueError('Square observed triangle of size >=4 required')
    n = len(c)
    mask = np.fromfunction(lambda i,j:i+j<n,c.shape,dtype=int)
    if not np.array_equal(np.isfinite(c),mask) or np.any(c[mask] < 0):
        raise ValueError('Complete finite nonnegative observed mask required')
    exposure = float(sum(c[i,n-i-1] for i in range(n)))
    if not math.isfinite(exposure) or exposure <= 0:
        raise ValueError('Positive finite latest-amount exposure required')
    try:
        fit = mack(c)
        point, se = float(fit['ibnr'].sum()), float(fit['total_std_error'])
        if not math.isfinite(point+se) or se < 0:
            raise ValueError('Nonfinite fitted moments')
    except (ValueError,FloatingPointError):
        return Forecast(0.,exposure,exposure,'fallback_failed_mack')
    floor = exposure * 1e-12
    return Forecast(point,max(se,floor),exposure,'scale_floor' if se<floor else 'ok',se)

def conformal_rank(n, level):
    if not isinstance(n,int) or n < 1 or level not in LEVELS:
        raise ValueError('Positive calibration size and registered level required')
    coverage = Fraction(level,100)
    x = (n+1)*coverage
    return (x.numerator+x.denominator-1)//x.denominator

def order_threshold(scores, level):
    scores = np.asarray(scores,dtype=float)
    if scores.ndim != 1 or len(scores)==0 or not np.all(np.isfinite(scores)) or np.any(scores<0):
        raise ValueError('Finite nonnegative calibration scores required')
    k = conformal_rank(len(scores),level)
    return float(np.sort(scores)[k-1]) if k<=len(scores) else math.inf

def fit_calibration(features, outcomes):
    if len(features)!=len(outcomes) or len(features)<2:
        raise ValueError('At least two separate calibration pairs required')
    y = np.asarray(outcomes,dtype=float)
    if not np.all(np.isfinite(y)):
        raise ValueError('Nonfinite calibration outcome')
    point=np.array([x.point for x in features]); scale=np.array([x.scale for x in features])
    if not np.all(np.isfinite(point)) or not np.all(np.isfinite(scale)) or np.any(scale<=0):
        raise ValueError('Invalid fixed score map')
    residual=y-point; z=residual/scale
    if not np.all(np.isfinite(residual)) or not np.all(np.isfinite(z)):
        raise ValueError('Nonfinite calibration arithmetic')
    return dict(n=len(y),fallback_calibration_cases=sum(x.status=='fallback_failed_mack' for x in features),
        scaled_bias=float(z.mean()),scaled_std=float(z.std(ddof=1)),
        absolute={str(l):order_threshold(abs(residual),l) for l in LEVELS},
        scaled={str(l):order_threshold(abs(z),l) for l in LEVELS},
        ranks={str(l):conformal_rank(len(y),l) for l in LEVELS})

def interval(f, calibration, method, level):
    if method not in METHODS or level not in LEVELS:
        raise ValueError('Unknown registered method/level')
    if f.status=='fallback_failed_mack':
        return (math.nan,math.nan,'failed') if method=='mack_normal' else (-math.inf,math.inf,'unbounded_fallback')
    z=float(norm.ppf((1+level/100)/2))
    if method=='mack_normal':
        center,radius=f.point,z*(f.raw_std_error if f.raw_std_error is not None else f.scale)
    elif method=='calibrated_normal':
        center=f.point+calibration['scaled_bias']*f.scale
        radius=z*calibration['scaled_std']*f.scale
    else:
        center=f.point
        radius=calibration['absolute'][str(level)] if method=='conformal_absolute' else calibration['scaled'][str(level)]*f.scale
    if math.isinf(radius): return -math.inf,math.inf,'unbounded_rank'
    if not math.isfinite(center+radius) or radius<0:
        raise ValueError('Nonfinite interval calculation')
    return center-radius,center+radius,'ok'

def score(actual, lower, upper, status, exposure, level):
    if not math.isfinite(actual) or not math.isfinite(exposure) or exposure<=0:
        raise ValueError('Invalid scoring target/exposure')
    if status=='failed':
        return dict(covered=False,width=math.inf,interval_score=math.inf,finite=False,failed=True)
    covered=lower<=actual<=upper
    if status.startswith('unbounded'):
        return dict(covered=covered,width=math.inf,interval_score=math.inf,finite=False,failed=False)
    if not math.isfinite(lower+upper) or lower>upper:
        raise ValueError('Invalid finite interval')
    alpha=1-level/100
    loss=upper-lower+(2/alpha)*(max(lower-actual,0)+max(actual-upper,0))
    return dict(covered=covered,width=(upper-lower)/exposure,interval_score=loss/exposure,finite=True,failed=False)
