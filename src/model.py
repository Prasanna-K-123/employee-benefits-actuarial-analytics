from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261005


def generate_pension_population(n: int = 180, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    age = rng.integers(25, 61, size=n)
    max_service = np.minimum(age - 21, 30)
    service = np.array([rng.integers(0, max(1, int(m) + 1)) for m in max_service])
    salary = rng.integers(40_000, 160_001, size=n).astype(float)
    return pd.DataFrame({
        "employee_id": [f"E{i+1:03d}" for i in range(n)],
        "age": age,
        "service_years": service,
        "salary": salary,
    })


def annuity_factor(rate: float, years: int) -> float:
    if rate == 0:
        return float(years)
    return float((1 - (1 + rate) ** (-years)) / rate)


def pension_valuation(
    employees: pd.DataFrame,
    discount_rate: float = 0.05,
    salary_growth: float = 0.04,
    accrual_rate: float = 0.015,
    retirement_age: int = 65,
    annuity_rate: float = 0.04,
    annuity_years: int = 15,
) -> pd.DataFrame:
    out = employees.copy()
    out["years_to_retirement"] = np.maximum(retirement_age - out["age"], 0)
    out["projected_final_salary"] = out["salary"] * (1 + salary_growth) ** out["years_to_retirement"]
    out["accrued_annual_benefit"] = accrual_rate * out["projected_final_salary"] * out["service_years"]
    af = annuity_factor(annuity_rate, annuity_years)
    out["pv_at_retirement"] = out["accrued_annual_benefit"] * af
    out["liability_proxy"] = out["pv_at_retirement"] / (1 + discount_rate) ** out["years_to_retirement"]
    return out


def pension_sensitivity(employees: pd.DataFrame) -> pd.DataFrame:
    scenarios = [
        ("Discount -100 bps", 0.04, 0.04),
        ("Base", 0.05, 0.04),
        ("Discount +100 bps", 0.06, 0.04),
        ("Salary growth -100 bps", 0.05, 0.03),
        ("Salary growth +100 bps", 0.05, 0.05),
    ]
    rows = []
    base = None
    for name, d, g in scenarios:
        total = pension_valuation(employees, discount_rate=d, salary_growth=g)["liability_proxy"].sum()
        if name == "Base":
            base = total
        rows.append({"scenario": name, "discount_rate": d, "salary_growth": g, "liability_proxy": float(total)})
    for row in rows:
        row["change_vs_base_pct"] = float(row["liability_proxy"] / base - 1)
    return pd.DataFrame(rows)


def pension_cashflows(valuation: pd.DataFrame, horizon: int = 15) -> pd.DataFrame:
    rows = []
    for year in range(1, horizon + 1):
        retiring = valuation[valuation["years_to_retirement"] == year]
        rows.append({
            "year": year,
            "new_retirees": int(len(retiring)),
            "annual_benefit_starting": float(retiring["accrued_annual_benefit"].sum()),
        })
    return pd.DataFrame(rows)


def de_risking_scenario(
    base_liability: float,
    eligible_share: float = 0.25,
    settlement_factor: float = 0.97,
) -> dict:
    settlement = base_liability * eligible_share * settlement_factor
    retained = base_liability * (1 - eligible_share)
    post = settlement + retained
    return {
        "eligible_share": eligible_share,
        "settlement_factor": settlement_factor,
        "pre_settlement_liability_proxy": base_liability,
        "post_settlement_liability_proxy": post,
        "proxy_reduction": base_liability - post,
        "proxy_reduction_pct": 1 - post / base_liability,
    }


def generate_health_triangle(months: int = 12, seed: int = SEED + 1):
    rng = np.random.default_rng(seed)
    ultimates = rng.normal(1_200_000, 150_000, size=months).clip(850_000, 1_600_000)
    cumulative_pattern = np.array(
        [0.28, 0.47, 0.62, 0.73, 0.81, 0.87, 0.91, 0.94, 0.965, 0.982, 0.994, 1.0]
    )
    if months != len(cumulative_pattern):
        raise ValueError("This educational example uses a 12x12 development pattern.")
    full = np.outer(ultimates, cumulative_pattern)
    triangle = np.full((months, months), np.nan)
    for i in range(months):
        observed = months - i
        triangle[i, :observed] = full[i, :observed]
    return triangle, ultimates, cumulative_pattern


def chain_ladder(triangle: np.ndarray) -> dict:
    n = triangle.shape[1]
    factors = []
    for j in range(n - 1):
        valid = ~np.isnan(triangle[:, j + 1])
        denominator = np.nansum(triangle[valid, j])
        numerator = np.nansum(triangle[valid, j + 1])
        factors.append(float(numerator / denominator))
    factors = np.array(factors)

    cdf = np.ones(n)
    for j in range(n - 2, -1, -1):
        cdf[j] = cdf[j + 1] * factors[j]

    latest = []
    latest_dev = []
    for row in triangle:
        idx = np.where(~np.isnan(row))[0][-1]
        latest_dev.append(int(idx))
        latest.append(float(row[idx]))

    latest = np.array(latest)
    latest_dev = np.array(latest_dev)
    ultimate = np.array([latest[i] * cdf[latest_dev[i]] for i in range(len(latest))])
    ibnr = ultimate - latest
    return {
        "age_to_age_factors": factors,
        "cumulative_development_factors": cdf,
        "latest_paid": latest,
        "estimated_ultimate": ultimate,
        "ibnr": ibnr,
    }


def health_reserve_summary(
    triangle: np.ndarray,
    pad_rate: float = 0.05,
    annual_trend: float = 0.07,
) -> dict:
    cl = chain_ladder(triangle)
    paid = float(cl["latest_paid"].sum())
    ultimate = float(cl["estimated_ultimate"].sum())
    ibnr = float(cl["ibnr"].sum())
    pad = ibnr * pad_rate
    reserve_with_pad = ibnr + pad
    next_year_cost_proxy = ultimate * (1 + annual_trend)
    return {
        "paid_to_date": paid,
        "estimated_ultimate": ultimate,
        "ibnr": ibnr,
        "pad_rate": pad_rate,
        "pad": pad,
        "reserve_with_pad": reserve_with_pad,
        "annual_claim_trend": annual_trend,
        "next_year_cost_proxy": next_year_cost_proxy,
    }


def health_sensitivity(triangle: np.ndarray) -> pd.DataFrame:
    rows = []
    for trend in [0.05, 0.07, 0.09]:
        s = health_reserve_summary(triangle, pad_rate=0.05, annual_trend=trend)
        rows.append({
            "scenario": f"Claim trend {trend:.0%}",
            "annual_claim_trend": trend,
            "ibnr": s["ibnr"],
            "reserve_with_pad": s["reserve_with_pad"],
            "next_year_cost_proxy": s["next_year_cost_proxy"],
        })
    return pd.DataFrame(rows)


def run(output_dir: str | Path = "outputs", data_dir: str | Path = "data") -> dict:
    output_dir = Path(output_dir)
    data_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    employees = generate_pension_population()
    employees.to_csv(data_dir / "synthetic_pension_population.csv", index=False)

    pension = pension_valuation(employees)
    pension.to_csv(output_dir / "pension_employee_valuation.csv", index=False)

    psens = pension_sensitivity(employees)
    psens.to_csv(output_dir / "pension_sensitivity.csv", index=False)

    pcash = pension_cashflows(pension)
    pcash.to_csv(output_dir / "pension_cashflow_forecast.csv", index=False)

    base_liability = float(pension["liability_proxy"].sum())
    derisk = de_risking_scenario(base_liability)

    triangle, _, _ = generate_health_triangle()
    tri_df = pd.DataFrame(triangle, columns=[f"dev_{i+1}" for i in range(triangle.shape[1])])
    tri_df.insert(0, "accident_month", [f"M{i+1:02d}" for i in range(triangle.shape[0])])
    tri_df.to_csv(data_dir / "synthetic_health_claims_triangle.csv", index=False)

    hsummary = health_reserve_summary(triangle)
    hsens = health_sensitivity(triangle)
    hsens.to_csv(output_dir / "health_claims_sensitivity.csv", index=False)

    summary = {
        "scope": "educational employee-benefits actuarial analytics; synthetic data only",
        "pension": {
            "employees": int(len(employees)),
            "base_liability_proxy": base_liability,
            "discount_minus_100bps_liability": float(
                psens.loc[psens.scenario == "Discount -100 bps", "liability_proxy"].iloc[0]
            ),
            "discount_plus_100bps_liability": float(
                psens.loc[psens.scenario == "Discount +100 bps", "liability_proxy"].iloc[0]
            ),
            "de_risking_proxy_reduction": derisk["proxy_reduction"],
            "de_risking_proxy_reduction_pct": derisk["proxy_reduction_pct"],
        },
        "health": hsummary,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

