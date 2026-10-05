import numpy as np

from src.model import (
    annuity_factor,
    chain_ladder,
    de_risking_scenario,
    generate_health_triangle,
    generate_pension_population,
    health_reserve_summary,
    pension_cashflows,
    pension_sensitivity,
    pension_valuation,
)


def test_annuity_factor_positive():
    assert annuity_factor(0.04, 15) > 0


def test_pension_discount_sensitivity_direction():
    employees = generate_pension_population()
    sens = pension_sensitivity(employees).set_index("scenario")
    assert sens.loc["Discount -100 bps", "liability_proxy"] > sens.loc["Base", "liability_proxy"]
    assert sens.loc["Discount +100 bps", "liability_proxy"] < sens.loc["Base", "liability_proxy"]


def test_pension_salary_growth_sensitivity_direction():
    employees = generate_pension_population()
    sens = pension_sensitivity(employees).set_index("scenario")
    assert sens.loc["Salary growth +100 bps", "liability_proxy"] > sens.loc["Base", "liability_proxy"]
    assert sens.loc["Salary growth -100 bps", "liability_proxy"] < sens.loc["Base", "liability_proxy"]


def test_pension_liabilities_nonnegative():
    v = pension_valuation(generate_pension_population())
    assert (v["liability_proxy"] >= 0).all()


def test_cashflow_horizon_and_nonnegative_benefits():
    v = pension_valuation(generate_pension_population())
    cash = pension_cashflows(v, horizon=15)
    assert len(cash) == 15
    assert (cash["annual_benefit_starting"] >= 0).all()


def test_derisking_proxy_reduces_liability_under_discounted_settlement():
    base = float(pension_valuation(generate_pension_population())["liability_proxy"].sum())
    result = de_risking_scenario(base, eligible_share=0.25, settlement_factor=0.97)
    assert result["post_settlement_liability_proxy"] < base
    assert result["proxy_reduction"] > 0


def test_chain_ladder_ibnr_nonnegative():
    tri, _, _ = generate_health_triangle()
    cl = chain_ladder(tri)
    assert np.all(cl["ibnr"] >= -1e-8)


def test_health_pad_increases_reserve():
    tri, _, _ = generate_health_triangle()
    s = health_reserve_summary(tri, pad_rate=0.05)
    assert s["reserve_with_pad"] > s["ibnr"]

