# Recalibration Brief — Liquidity Scoring & Return Ladder Validation

## Objective

The current optimizer produces counterintuitive portfolio allocations:
- Balanced portfolio has 0% Aave — it should be the transition instrument
- Max Yield is dominated by Aave rather than Pendle YT/PT
- The frontier appears to jump from off-chain directly to on-chain without a logical stepping stone

The root cause is likely miscalibrated liquidity scores producing a broken risk-adjusted return ladder. This brief fixes that.

**This brief covers two things only:**
1. Liquidity score recalibration — derived from observable data, not judgment calls
2. Return ladder validation — verify net risk-adjusted returns are in the correct order after recalibration

**This brief does NOT touch:**
- Exploit haircut methodology — stays as designed
- Optimizer constraint logic — already fixed in the previous sanity check
- Raw yield inputs — manually sourced data files stay untouched (`sbn_yields.csv`, `rdpu_nav.csv`, `usd_idr_rate.csv`)

---

## Background — How the Haircut Works

The risk-adjusted yield formula is:

```
RAY = Yield_Raw - Liquidity_Haircut - (P_Exploit × S_Severity)
```

**This brief is concerned with the Liquidity Haircut only.** The exploit haircut is not being changed.

The liquidity haircut is a basis point penalty mapped from a 1–5 liquidity score:

| Score | Penalty |
|---|---|
| 5 | 0 bps |
| 4 | 5 bps |
| 3 | 15 bps |
| 2 | 30 bps |
| 1 | 60 bps |

The problem is not the penalty scale — the problem is that the scores assigned to each instrument may not reflect observable market data. This brief replaces judgment-call scores with data-derived scores.

---

## Instrument Universe

Six instruments are evaluated for liquidity scoring. Note that Aave USDC and Aave USDT are treated as a **single combined `aave` allocation** in the optimizer — they are not separate instruments. The USDC/USDT split is an internal implementation note, not an optimizer variable.

| ID | Instrument | Currency |
|---|---|---|
| `mmf` | RDPU (Indonesian Money Market Fund) | IDR |
| `sbn` | SBN short-term < 1yr | IDR |
| `aave` | Aave USDC + USDT pool (combined) | USD |
| `pendle_pt` | Pendle PT stablecoin pools | USD |
| `pendle_yt` | Pendle YT stablecoin pools | USD |

---

## Target Liquidity Score Ladder

The following ladder must hold after recalibration. It is non-negotiable — it reflects both market structure reality and treasury practitioner judgment:

```
MMF (5) > SBN (4) = Aave combined (4) > Pendle PT (3) > Pendle YT (2)
```

| Instrument | Target Score | Basis Point Penalty | Rationale |
|---|---|---|---|
| MMF (RDPU) | 5 | 0 bps | Daily NAV redemption, no exit friction |
| SBN | 4 | 5 bps | Secondary market exists but bid-ask spread on short tenors is wide |
| Aave USDC | 4 | 5 bps | Instant withdrawal under normal utilization |
| Aave USDT | 3 | 15 bps | Same pool depth as USDC but carries stablecoin counterparty risk in stress |
| Aave combined | 4 | 5 bps | Weighted toward USDC; score reflects USDC-dominant split |
| Pendle PT | 3 | 15 bps | AMM exit required; pool depth limits large exits |
| Pendle YT | 2 | 30 bps | Shallowest AMM pools; value decays to zero at maturity, reducing buyer interest |

**Note on Aave USDT:** Although scored 3 individually, the combined `aave` instrument is scored 4 because the allocation is expected to be USDC-dominant. If the agent determines the USDT share exceeds 40% of the combined Aave allocation, downgrade the combined score to 3 and flag explicitly.

---

## Step 1 — Derive Scores from Observable Data

Scores must be derived from data, not assigned as assumptions. Use the following methodology for each instrument.

### MMF (RDPU) — Score 5, confirmed, no data check required
Daily NAV redemption is a regulatory requirement under OJK. Score is structural, not market-dependent.

### SBN — Score 4, confirm via spread data
Check whether short-tenor SBN (< 1yr) bid-ask spread data is available in `sbn_yields.csv` or any supplementary source. If spread data is unavailable, score 4 is accepted as a documented assumption. Flag explicitly if assumed.

### Aave USDC — Data-derived score
Pull utilization rate history from `aave_tvl.csv` or DeFiLlama yields endpoint.

Compute:
```
liquidity_failure_rate = days where utilization > 95% / total days
```

Scoring rule:
- failure_rate < 2% → Score 4
- failure_rate 2–5% → Score 3
- failure_rate > 5% → Score 2

For a $3M position against Aave's multi-billion USDC pool, exit slippage is zero under normal conditions. Slippage check is not required for this position size.

### Aave USDT — Data-derived score
Same methodology as USDC. Additionally note that USDT carries stablecoin counterparty risk (Tether reserve opacity) that increases tail risk in stress scenarios. Apply a one-notch downgrade from the USDC score regardless of utilization data.

### Pendle PT — Data-derived score
Pull pool TVL from `pendle_tvl.csv`. Estimate exit slippage for a $3M position using constant-product AMM approximation:

```
slippage_bps = (exit_size / pool_tvl) × 10000 × 0.5
```

Scoring rule:
- slippage < 10 bps → Score 4
- slippage 10–25 bps → Score 3
- slippage > 25 bps → Score 2

Use the median pool TVL over the last 90 days, not the current snapshot.

### Pendle YT — Data-derived score
Same methodology as Pendle PT. Expect YT pools to be shallower than PT pools. Additionally apply a one-notch downgrade from the PT score to reflect value decay risk (YT decays to zero at maturity, reducing buyer interest and making large exits harder as maturity approaches).

---

## Step 2 — Update protocol_params.json

After deriving scores from data, update `protocol_params.json` with:
- The new liquidity score for each instrument
- The data source used to derive it
- A flag if any score was assumed rather than data-derived

Do not change any exploit parameters (p, s values). Those are out of scope for this brief.

Re-run `src/risk_adjustment.py` to produce updated `risk_adjusted_returns.csv`.

---

## Step 3 — Validate the Return Ladder

After recalibration, print the net risk-adjusted annualized return (IDR) for all five instruments and verify the following strict ordering holds:

```
mmf < sbn < aave < pendle_pt < pendle_yt
```

If the ladder is broken at any step, do not proceed to re-running the optimizer. Report which step is broken and what the values are. The ladder must be fixed before optimization.

Expected approximate ranges after correct calibration:

| Instrument | Expected Net Return (IDR) |
|---|---|
| mmf | ~5.5–6.5% |
| sbn | ~6.0–7.0% |
| aave | ~7–10% |
| pendle_pt | ~10–14% |
| pendle_yt | ~14–20% |

If any instrument falls outside these ranges, flag it and report the raw yield and haircut components separately so the source of the deviation can be identified.

---

## Step 4 — Re-run Pipeline from Notebook 02 Onward

Once the return ladder is confirmed, re-run in this order:

```
02_risk_adjustment → 03_covariance_regime → 04_cvar_optimization → 05_output_visualization
```

Do not re-run notebooks 00 or 01. Do not modify raw data files.

---

## Step 5 — Validation Criteria

The recalibrated output must satisfy all of the following:

### Return ladder
- Strict ordering: mmf < sbn < aave < pendle_pt < pendle_yt
- No instrument outside the expected range table above

### Named portfolio composition
The three portfolios must tell a coherent conservative / balanced / aggressive story:

| Portfolio | Expected Composition |
|---|---|
| Min Risk | >80% MMF + SBN combined, minimal or zero on-chain exposure |
| Balanced | MMF/SBN anchor (40–60%) + Aave entry (10–25%) + Pendle PT (10–20%) + small YT |
| Max Yield | Pendle YT at or near 15% cap + heavy Pendle PT (40–50%) + Aave remainder |

### Frontier integrity
- 100 portfolios, monotonically increasing expected return
- CVaR worsens (becomes more negative or less positive) from min to max
- No negative weights larger than 1e-6 in absolute value
- Pendle YT ≤ 15% in all portfolios
- No single instrument > 50% in any portfolio

### Output files to deliver
Report the following after recalibration is complete:
1. Updated `protocol_params.json` — showing new liquidity scores and data sources
2. Updated `risk_adjusted_returns.csv` — showing the corrected return ladder
3. New `named_portfolios.json` — showing the corrected portfolio compositions
4. Frontier summary table — first 5 rows, middle 5 rows, last 5 rows of `frontier_portfolios.csv`

---

## Notes for Agent

- The liquidity score ladder (MMF=5, SBN=4, Aave=4, Pendle PT=3, Pendle YT=2) is the target outcome. If data-derived scores conflict with this ladder, flag the conflict and report the data — do not silently override the data to match the target.
- Aave USDT is scored separately for documentation purposes but feeds into the single combined `aave` instrument in the optimizer.
- If Pendle pool TVL data is insufficient for the slippage calculation, use score 3 for PT and score 2 for YT as documented assumptions and flag explicitly.
- Do not modify the stress covariance parameters — the 3x volatility amplification and 0.75 correlation floor are out of scope.
- If the return ladder cannot be achieved without modifying raw yield inputs, stop and report. Do not modify raw data files under any circumstances.
