# Sanity Check Brief — Yield Optimization Model

## Problem Statement

`named_portfolios.json` shows a degenerate optimizer result. All three named portfolios (min_risk, balanced, max_yield) converge to ~50% Pendle PT / ~50% Pendle YT with all other instruments at effectively zero. CVaR and expected return are nearly identical across all three. This is not an efficient frontier — it is a single corner solution repeated three times.

Two confirmed issues, possibly more:

- **Issue 1 — Constraint violation:** Pendle YT weight is ~50% in all portfolios. The model spec requires a hard cap of 15% on Pendle YT. This constraint is not being enforced.
- **Issue 2 — Frontier collapse:** The optimizer is finding one dominant solution and not moving off it across the return target sweep. This means either the expected return inputs are so skewed that Pendle instruments dominate unconditionally, or the return target sweep is not spanning a meaningful range, or both.

---

## Step 1 — Audit the Inputs

Print `risk_adjusted_returns.csv` in full and report the net risk-adjusted annualized return (in IDR) for each instrument: `mmf`, `sbn`, `aave`, `pendle_pt`, `pendle_yt`.

Check whether Pendle PT and YT returns are plausibly higher than mmf/sbn but not so extreme they crowd everything out. Rough sanity benchmarks:

| Instrument | Expected Net Return (IDR) |
|---|---|
| mmf (RDPU) | ~5.5–6.5% |
| sbn | ~6.0–7.0% |
| aave | ~7–10% |
| pendle_pt | ~10–14% |
| pendle_yt | ~14–20% (before risk haircut) |

If `pendle_pt` and `pendle_yt` net returns are above 18% while `mmf`/`sbn` are below 7%, the optimizer will always go all-in on Pendle. That is the root cause.

---

## Step 2 — Audit the Constraints in optimizer.py

Open `src/optimizer.py` and verify each of the following constraints exists and is correctly formulated in CVXPY:

```python
# Required constraints — verify all five exist
weights >= 0                          # no short positions
cp.sum(weights) == 1                  # fully invested
weights <= 0.50                       # max 50% single instrument
weights[pendle_yt_index] <= 0.15      # max 15% Pendle YT — THIS IS LIKELY MISSING
```

Report exactly what constraints are present. Paste the constraints block verbatim.

---

## Step 3 — Audit the Return Target Sweep

In the frontier construction loop, report:

- What is the minimum target return used?
- What is the maximum target return used?
- How many steps (should be 100)?
- Is the sweep linear between min and max?

The min target should be close to the lowest single-instrument return (roughly mmf ~6%). The max target should be close to the highest feasible portfolio return given constraints. If both endpoints are set incorrectly the frontier will be flat.

---

## Step 4 — Fix and Re-run

Apply fixes in this order:

**Fix 1 — Add the missing YT constraint** if absent:

```python
weights[pendle_yt_index] <= 0.15
```

**Fix 2 — Recalibrate return targets** if inputs are degenerate. If Pendle returns are unrealistically high, check the mean reversion blend in `normalization.py` — the 40/60 spot/historical blend may be producing inflated forward estimates for Pendle YT. Cap Pendle YT net expected return at a maximum of 20% annualized IDR as a sanity ceiling.

**Fix 3 — Re-run the full pipeline from notebook 02 onward** (risk adjustment → covariance → optimization → visualization) and produce new output files.

---

## Step 5 — Validation Criteria

The fixed output must satisfy all of the following before being accepted:

| Check | Requirement |
|---|---|
| `named_portfolios.json` | Three portfolios with meaningfully different weights and CVaR values |
| min_risk portfolio | >40% combined mmf + sbn allocation |
| balanced portfolio | Meaningful allocation across at least 3 instruments |
| max_yield portfolio | pendle_yt weight ≤ 0.15 |
| CVaR progression | Must worsen (more negative) from min_risk → max_yield |
| Return progression | Must increase from min_risk → max_yield |
| Weights | No negative weights (numerical noise <1e-6 acceptable, anything larger is not) |
| `frontier_portfolios.csv` | 100 rows, monotonically increasing expected return, monotonically worsening CVaR |

Report the new `named_portfolios.json` and a summary table of the frontier (first 5 rows, middle 5 rows, last 5 rows) after fixes are applied.

---

## Notes for Agent

- Do not skip Step 1. The input audit is the most important diagnostic. If the inputs are wrong, fixing the constraint alone will not produce a meaningful frontier.
- Do not re-run notebook 00 or 01. Start from 02 onward after fixes are applied.
- Do not modify `sbn_yields.csv`, `rdpu_nav.csv`, or `usd_idr_rate.csv` — these are manually sourced and must remain untouched.
- Flag explicitly if the fallback stress covariance is triggered (fewer than 30 stress observations).
