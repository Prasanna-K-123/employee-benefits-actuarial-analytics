import numpy as np
import pytest
from src.stochastic_reserving import load_raa, mack, diagonal_backtest


def test_mack_published_raa_standard_errors():
    triangle, _ = load_raa()
    fit = mack(triangle)
    # Rounded external reference: Mack (1994), p.130; independently mirrored
    # in casact/chainladder-python's test_mack1994_hardcode.
    published = [206, 623, 747, 1469, 2002, 2209, 5358, 6333, 24566]
    np.testing.assert_allclose(fit['origin_std_error'][1:], published, atol=1, rtol=0)
    np.testing.assert_allclose(fit['sigma_squared'][:8], [27883,1109,691,61.2,119,40.8,1.34,7.88], atol=1, rtol=0)
    assert fit['ibnr'].sum() == pytest.approx(52135.228, abs=.01)


def test_scale_equivariance_and_shared_parameter_risk():
    c, _ = load_raa()
    a, b = mack(c), mack(c*7)
    np.testing.assert_allclose(a['factors'], b['factors'])
    np.testing.assert_allclose(b['ibnr'], a['ibnr']*7)
    assert b['total_std_error'] == pytest.approx(a['total_std_error']*7)
    assert a['total_std_error']**2 > np.sum(a['origin_std_error']**2)


def test_backtest_does_not_fit_future_diagonal():
    c, years = load_raa()
    before = diagonal_backtest(c, years)
    changed = c.copy()
    # Change a revealed 1990 outcome: earlier-cutoff forecasts cannot change.
    changed[8, 1] *= 10
    after = diagonal_backtest(changed, years)
    np.testing.assert_allclose(before.chain_ladder_next, after.chain_ladder_next)
    assert not np.array_equal(before.actual_next, after.actual_next)


def test_malformed_triangle_rejected():
    c, _ = load_raa()
    c[3, 2] = np.nan
    with pytest.raises(ValueError):
        mack(c)
