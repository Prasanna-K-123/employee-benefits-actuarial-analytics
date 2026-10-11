import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm
from src.stochastic_reserving import load_raa
from src.predictive_reserving import (PROBS,parts,one_step_moments,moment_quantiles,positive_draw,
    shared_projection,interval_score,score_row,public_diagonals,complete_simulation,
    calibration_summary,order_bracket,load_public)


def test_invalid_observed_simulation_records_every_failed_method(monkeypatch):
    import src.predictive_reserving as module
    c=noiseless();c[2,0]=0
    monkeypatch.setattr(module,'complete_simulation',lambda case,seed:(c,12.))
    rows=module.calibration_case(0,0,16)
    assert len(rows)==4
    assert all(r['status']=='failed' and r['actual']==12 and r['point'] is None for r in rows)
    assert all(r['observed_zero_cells']==1 for r in rows)


def noiseless():
    return np.array([[100.,200.,250.,275.],[120.,240.,300.,np.nan],
                     [140.,280.,np.nan,np.nan],[160.,np.nan,np.nan,np.nan]])


def test_independent_hand_counted_one_step_moments():
    # Historical x=10,20,30; z=20,50,90 gives f=8/3, sigma2=25/6.
    mu,var=one_step_moments(40,8/3,25/6,60)
    assert mu==pytest.approx(320/3)
    assert var==pytest.approx(2500/9)


def test_normal_quantiles_include_negative_values_without_clipping():
    q=moment_quantiles(1,100,'normal')
    np.testing.assert_allclose(q,1+10*norm.ppf(PROBS))
    assert q[0]<0


def test_lognormal_parameters_match_mean_and_variance():
    mean,var=20.,49.
    v=np.log(1+var/mean**2);mu=np.log(mean)-v/2
    assert np.exp(mu+v/2)==pytest.approx(mean)
    assert (np.exp(v)-1)*np.exp(2*mu+v)==pytest.approx(var)
    np.testing.assert_allclose(moment_quantiles(mean,var,'lognormal'),np.exp(mu+np.sqrt(v)*norm.ppf(PROBS)))


@pytest.mark.parametrize('family',['gamma','lognormal'])
def test_simulated_conditional_moments_against_hand_oracle(family):
    values=positive_draw(np.full(100000,20.),np.full(100000,49.),np.random.default_rng(983),family)
    assert values.mean()==pytest.approx(20,rel=.004)
    assert values.var()==pytest.approx(49,rel=.025)


@pytest.mark.parametrize('family',['gamma','lognormal'])
def test_zero_dispersion_no_hidden_sampling(family):
    c=noiseless();fit=parts(c);d=shared_projection(c,16,[52],family)
    np.testing.assert_allclose(d['reserve'],fit['ibnr'].sum())
    assert d['expected_conditional_process_variance']==pytest.approx(0,abs=1e-20)
    assert d['shared_parameter_variance']==pytest.approx(0,abs=1e-20)


def test_hand_interval_score_keeps_losses():
    assert interval_score(15,2,10,.2)==58
    assert interval_score(0,2,10,.2)==28
    assert interval_score(6,2,10,.2)==8


def test_score_boundary_inclusion_and_fixed_denominators():
    q=np.array([1,2,3,4,5,6,7.])
    assert score_row(1,q,10)['cover95']
    assert not score_row(1,q,10)['cover80']


def test_quantile_mc_bracket_is_ordered_and_unclipped():
    r=order_bracket(np.arange(-512,512),.025)
    assert r['lower_rank']<r['upper_rank']
    assert r['lower']<r['upper']<0


def test_later_outcome_never_changes_earlier_forecast():
    c,years=load_raa();before=public_diagonals(c,years)
    c[8,1]*=10;after=public_diagonals(c,years)
    np.testing.assert_array_equal(before.chain_ladder,after.chain_ladder)
    np.testing.assert_array_equal(before.q025,after.q025)
    assert not np.array_equal(before.actual,after.actual)


def test_original_22_eligible_cells_and_training_pair_count():
    c,years=load_raa();d=public_diagonals(c,years)
    assert len(d[(d.scope=='cell')&(d.method=='mack_normal')])==22
    assert (d.fit_rows>=2).all()
    assert len(d[(d.scope=='eligible_diagonal')&(d.method=='mack_normal')])==4


def test_future_shock_cannot_change_observed_design():
    a,ta=complete_simulation('independent_lognormal',[721])
    b,tb=complete_simulation('future_calendar_shock',[721])
    np.testing.assert_array_equal(a,b)
    assert tb>ta


def test_seed_reconstruction_is_deterministic():
    a,ya=complete_simulation('independent_gamma',[61])
    b,yb=complete_simulation('independent_gamma',[61])
    np.testing.assert_array_equal(a,b);assert ya==yb


def test_positive_cumulative_can_have_negative_increments():
    c,_=load_raa();assert np.any(np.diff(c[1,:9])<0)
    assert np.isfinite(parts(c)['total_std_error'])


def test_zero_gamma_process_states_retained_without_floor_or_redraw():
    a=positive_draw(np.array([0.,1e-200]),np.array([0.,1e-199]),np.random.default_rng(41),'gamma')
    assert np.array_equal(a,[0.,0.])


@pytest.mark.parametrize('family',['gamma','lognormal'])
def test_scale_equivariance_of_full_simulation(family):
    c,_=load_raa();a=shared_projection(c,256,[882],family);b=shared_projection(7*c,256,[882],family)
    np.testing.assert_allclose(b['reserve'],7*a['reserve'],rtol=2e-10,atol=2e-8)
    assert b['total_mixture_variance']==pytest.approx(49*a['total_mixture_variance'],rel=2e-10)


def test_shared_parameter_risk_contains_cross_origin_covariance():
    c,_=load_raa();d=shared_projection(c,4096,[481],'lognormal')
    assert d['shared_parameter_variance']>0
    assert d['expected_conditional_process_variance']>0
    assert d['total_mixture_variance']==d['shared_parameter_variance']+d['expected_conditional_process_variance']


def test_method_failure_remains_in_coverage_denominator():
    df=pd.DataFrame([dict(scenario='example',method='m',status='ok',cover80=True,cover95=True,
        score80_scaled=1.,score95_scaled=2.,width80_scaled=.5,width95_scaled=.8,upper95_exceeded=False),
        dict(scenario='example',method='m',status='failed')])
    r=calibration_summary(df)[0]
    assert r['cases']==2 and r['failed']==1 and r['coverage95']==.5
    assert r['score_denominator']==1


def test_duplicate_keys_and_incomplete_masks_fail_closed(tmp_path):
    p=tmp_path/'bad.csv';p.write_text('origin,development,values\n1981,1981,10\n1981,1981,11\n')
    with pytest.raises(ValueError):load_public(p)


@pytest.mark.parametrize('mean,var,family',[(0,1,'lognormal'),(5,-1,'normal'),(5,1,'unknown')])
def test_invalid_distribution_is_not_silently_repaired(mean,var,family):
    with pytest.raises(ValueError):moment_quantiles(mean,var,family)
