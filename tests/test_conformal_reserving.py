import itertools
import math
from fractions import Fraction
import numpy as np
import pytest
from src.conformal_reserving import (Forecast,forecast,conformal_rank,order_threshold,fit_calibration,interval,score,LEVELS,METHODS)

def triangle():
    c=np.full((4,4),np.nan)
    for i in range(4):
        for j in range(4-i):c[i,j]=(100+20*i)*1.2**j
    return c

@pytest.mark.parametrize('n',[1,2,9,19,20,99,512])
@pytest.mark.parametrize('level',LEVELS)
def test_rank_matches_exact_fraction_ceiling(n,level):
    x=Fraction((n+1)*level,100)
    assert conformal_rank(n,level)==math.ceil(x)

def test_small_calibration_requires_infinite_interval():
    assert math.isinf(order_threshold([1.,2.],95))

def test_ties_inclusive_and_order_invariant():
    a=[1.]*20
    assert order_threshold(a,95)==1.
    assert order_threshold(a[::-1],95)==1.

def test_complete_rank_enumeration():
    # All choices of the held-out score in an exchangeable multiset; every
    # permutation has the same set of ranks. This catches n vs n+1 errors.
    for level in LEVELS:
        total=20; scores=list(range(total)); covered=0
        for held in range(total):
            cal=[s for j,s in enumerate(scores) if j!=held]
            covered+=scores[held]<=order_threshold(cal,level)
        assert Fraction(covered,total)>=Fraction(level,100)

@pytest.mark.parametrize('bad',[[],[-1.,2.],[math.nan,1.],[math.inf,1.]])
def test_invalid_scores_refused(bad):
    with pytest.raises(ValueError):order_threshold(bad,95)

def test_forecast_never_accepts_future_cells():
    c=triangle();f=forecast(c)
    assert math.isfinite(f.point) and f.scale>0
    c[3,3]=1e9
    with pytest.raises(ValueError):forecast(c)

def test_zero_observed_fit_failure_retained():
    c=triangle();c[0,1]=0.;f=forecast(c)
    assert f.status=='fallback_failed_mack'
    for method in METHODS:
        lo,hi,status=interval(f,{},method,95)
        s=score(10.,lo,hi,status,f.exposure,95)
        assert s['covered']==(method!='mack_normal')
        assert not s['finite']

def test_units_and_width_scale_together():
    features=[Forecast(float(i),2.+i/20,100.,'ok') for i in range(20)]
    y=np.array([f.point+(-1)**i*(i+1)/10 for i,f in enumerate(features)])
    cal=fit_calibration(features,y)
    large=[Forecast(f.point*1000,f.scale*1000,f.exposure*1000,f.status) for f in features]
    cal_large=fit_calibration(large,y*1000)
    f=Forecast(8.,3.,120.,'ok');fl=Forecast(8000.,3000.,120000.,'ok')
    for method in METHODS:
        for level in LEVELS:
            lo,hi,status=interval(f,cal,method,level)
            lol,hil,sl=interval(fl,cal_large,method,level)
            assert sl==status
            assert np.allclose([lol,hil],np.array([lo,hi])*1000)

def test_evaluation_labels_cannot_change_calibration():
    features=[Forecast(10.,2.,100.,'ok') for _ in range(20)]
    cal=fit_calibration(features,np.arange(20.));before=repr(cal)
    for actual in [-1e10,0.,1e10]:
        lo,hi,status=interval(features[0],cal,'conformal_scaled',95)
        score(actual,lo,hi,status,100.,95)
    assert repr(cal)==before

def test_no_negative_reserve_clipping():
    f=Forecast(-100.,2.,100.,'ok');features=[f]*20
    cal=fit_calibration(features,np.arange(20.)-110)
    lo,hi,status=interval(f,cal,'conformal_absolute',95)
    assert lo<0 and hi<0 and score(-100.,lo,hi,status,100.,95)['covered']

def test_failure_scores_keep_denominator_visible():
    s=score(3.,math.nan,math.nan,'failed',100.,95)
    assert not s['covered'] and s['failed'] and math.isinf(s['interval_score'])

def test_ordered_nominal_levels():
    features=[Forecast(10.,2.,100.,'ok') for _ in range(20)]
    cal=fit_calibration(features,np.arange(20.))
    for method in METHODS:
        bounds=[interval(features[0],cal,method,l)[:2] for l in LEVELS]
        assert all(bounds[i+1][0]<=bounds[i][0] and bounds[i+1][1]>=bounds[i][1] for i in range(2))

def test_independent_scalar_oracle_hand_constant_triangle():
    from verify_conformal_reserving import scalar_mack
    c=np.full((4,4),np.nan)
    for i in range(4):
        for j in range(4-i):c[i,j]=100.*2**j
    point,scale,exposure,status,se=scalar_mack(c)
    assert point==1700. and exposure==1500. and se==0.
    f=forecast(c)
    assert f.point==point and f.scale==scale and f.raw_std_error==se
    lo,hi,st=interval(f,{},'mack_normal',95)
    assert lo==hi==1700. and st=='ok'

def test_invalid_forecast_refused():
    for kwargs in ({'scale':0.},{'point':math.inf},{'status':'unknown'},{'raw_std_error':-1.}):
        params=dict(point=1.,scale=1.,exposure=100.,status='ok');params.update(kwargs)
        with pytest.raises(ValueError):Forecast(**params)
