# 💰 Yield Generation & Optimization Model

**Portfolio Project by Gilang Fajar Wijayanto**  
Senior Treasury & Finance Operations Specialist | CFA Level I | FRM Part I  
[delomite.com](https://delomite.com) | [LinkedIn](https://www.linkedin.com/in/gilang-fajar-6973119a/)

---

## 📋 Overview

This repository demonstrates a **production-grade Yield Optimization Model** designed for institutional treasuries and digital asset exchanges. It solves the critical challenge of capital allocation across a fragmented yield landscape by unifying traditional IDR-based instruments (SBN, MMF) and on-chain USD-based DeFi protocols (Aave, Pendle) into a single, risk-adjusted framework.

### Business Context
Treasury managers in high-growth fintechs face a dual-world dilemma:
1. **Traditional World**: Low volatility, IDR-denominated instruments like MMF (4.5%) or SBN (5.5%).
2. **On-Chain World**: High yield, USD-denominated DeFi assets like Pendle (18-20%).

**The Challenge**: How to capture double-digit crypto yields without exposing the principal to excessive tail risk or smart-contract exploit events.

### Key Features
- ✅ **Unified Yield Normalization**: Annualizes and converts all yields to IDR terms, accounting for FX drift and protocol costs.
- ✅ **Multi-Factor Risk Haircuts**: Applies empirical discounts based on smart-contract exploit probability (p) and severity (s).
- ✅ **Systemic Stress Modeling**: Blends normal and stress covariance matrices using a 15% stress-state probability.
- ✅ **CVaR Optimization**: Uses Conditional Value at Risk (Expected Tail Loss) as the objective function to prioritize principal protection.
- ✅ **Regime-Aware Correlation**: Models "liquidity contagion" by forcing 0.75 cross-asset correlation during stress events.
- ✅ **Automated Pipeline**: End-to-end Python pipeline from DeFiLlama ingestion to Plotly-based visualization.

---

## 📊 System Metrics (Refined Optimization)

| Metric | Min Risk | Balanced | Max Yield |
|--------|----------|----------|-----------|
| **Expected Yield (IDR)** | **5.16%** | **8.51%** | **12.44%** |
| **95% CVaR (Loss)** | **-3.39%** (Gain) | **-1.08%** (Gain) | **+7.64%** (Loss) |
| **Pendle YT Exposure** | 1.3% | 15.0% | 14.8% |
| **MMF + SBN Weight** | 98.7% | 69.2% | 0.5% |
| **Aave Exposure** | 0.0% | 0.0% | 34.5% |

### Strategy Assessment
- **Min Risk**: Prioritizes principal safety. Even in the worst 5% of systemic scenarios, the portfolio targets a positive yield (+3.38%), anchored by high Indonesian base rates.
- **Max Yield**: Aggressive allocation within regulatory constraints. Strictly respects the 15% Pendle YT cap and 50% single-protocol limit.

---

## 📐 Methodology

### 1. Risk-Adjusted Yield (RAY)
Theoretical yield is haircutted based on technical and operational risks:
```
RAY = Yield_Raw - (P_Exploit × S_Severity) - Liquidity_Haircut
```

### 2. Systemic stress Fallback
During stress regimes (triggered by >15% TVL drops), the model assumes:
- **Volatility Amplification**: 2x multiplier for off-chain, 3x for crypto assets.
- **Correlation Ceiling**: All correlations floor at 0.75 (systemic shock).
- **Volatility Floor**: Minimum 2% annual vol for SBN, 5% for Crypto.

### 3. CVaR Sign Convention
This model follows the **industry consensus** (as seen in Investopedia):
- **Positive CVaR (+)**: Represents the **Expected Tail Loss**. A value of 3% means you expect to lose 3% on average in the worst 5% of scenarios.
- **Negative CVaR (-)**: Represents an **Expected Tail Gain**. A negative value means even in the worst 5% of scenarios, the portfolio is expected to remain profitable.

---

## 🗂️ Project Structure

```
yield-optimizer/
├── data/                          # Pipeline data storage
│   ├── raw/                       # TVL and Yield snapshots (DeFiLlama)
│   └── processed/                 # Normalization and model results
│       ├── frontier_portfolios.csv
│       ├── named_portfolios.json
│       └── charts/                # Generated visualizations
│
├── notebooks/                     # Exploratory analysis
│   └── *.ipynb                    # Step 00 to 05 execution sequence
│
├── src/                           # Business logic (RAY, Normalization, Optimizer)
│   ├── risk_adjustment.py
│   ├── covariance.py
│   └── optimizer.py               # CVXPY implementation
│
├── scripts/                       # Automation scripts
│   ├── re_run_pipeline.py         # 1-click execution
│   └── generate_charts.py         # Plotly visualization engine
│
├── requirements.txt               # Dependencies (cvxpy, plotly, pandas)
└── README.md                      # This file
```

---

## 🚀 Getting Started

### 1. Installation
```bash
git clone https://github.com/yourusername/yield-optimizer.git
cd yield-optimizer
pip install -r requirements.txt
```

### 2. Run the Model
You can execute the entire optimization pipeline with a single command:
```bash
python3 scripts/re_run_pipeline.py
```
This script runs the risk adjustment, calculates the amplified systemic covariance, solves 100 frontier points, and generates final visualizations.

### 3. View Results
Final portfolio details are saved in `data/processed/named_portfolios.json`.
Interactive charts (PNG) are available in `data/processed/charts/`.

---

## 📈 Technical Implementation Details

### CVaR Formulation in CVXPY
The model solves the following optimization problem for each target yield:
```python
minimize(zeta + (1 / (1 - confidence)) * sum(tail_loss) / num_scenarios)
subject to:
    weights >= 0
    sum(weights) == 1
    expected_returns @ weights >= target_yield
    weights[yt_index] <= 0.15 # Pendle YT Cap
```

### Synthetic Scenario Sampling
Because historical data often misses "black swan" events, the model generates **30,000 synthetic scenarios** via Multivariate Normal sampling from the blended systemic covariance matrix. This ensures the tail is sufficiently populated with stress events.

---

## 🎯 Use Cases
- **Treasury Management**: Safely allocating idle stablecoin or fiat reserves.
- **Yield Farming Strategy**: Optimizing Pendle and Aave exposure.
- **Risk Reporting**: Quantifying the systemic tail risk of a crypto-trad mix.
- **Audit Compliance**: Providing a math-first justification for protocol concentration limits.

---

## 🤝 Contact

**Gilang Fajar Wijayanto**  
📧 gilang.f@delomite.com  
🌐 [delomite.com](https://delomite.com)  
💼 [LinkedIn](https://www.linkedin.com/in/gilang-fajar-6973119a/)

---
## 📊 Recalibration Brief Results

- Updated liquidity scores applied per data‑driven calculations.
- `protocol_params.json` refreshed with new scores.
- `risk_adjusted_returns.csv` generated and validated.
- Frontiers re‑computed; see `data/processed/frontier_portfolios.csv`.
- Charts (`efficient_frontier.png`, `allocation_stack.png`) added to `data/processed/charts/`.

---

*Disclaimer: This project is for institutional portfolio research and software demonstration. The performance results are based on synthetic data and modeling assumptions and do not represent financial advice.*
