# 💰 Yield Generation & Optimization Model

A professional FinOps/Treasury model designed for crypto exchanges and institutional investors to optimize yield across a mix of traditional (IDR) and on-chain (USD) instruments.

This repository implements a **CVaR-based Efficient Frontier** pipeline that converts volatile yields into risk-adjusted, unified metrics to support strategic capital allocation.

## 🌟 Key Features

- **Unified Yield Normalization**: Seamlessly blends off-chain Indonesian instruments (SBN, MMF) with on-chain protocols (Aave, Pendle).
- **Multi-Factor Risk Haircuts**: Accounts for smart-contract exploit probabilities and liquidity exit costs.
- **Regime-Aware Modeling**: Dynamically adjusts covariance matrices based on market stress indicators (TVL drops).
- **CVaR Optimization**: Uses Conditional Value at Risk as the primary objective to prioritize downside protection over simple variance reduction.
- **Python-Native Pipeline**: Fully automated data fetching, normalization, and optimization via `cvxpy`.

## 📊 Core Performance Metrics

The model outputs three distinct target portfolios:

| Portfolio | Expected Yield (IDR) | 95% CVaR | Strategy Focus |
|-----------|----------------------|----------|----------------|
| **Min Risk** | ~4.5% | -4.5% | High Liquidity, Low Volatility (MMF / Aave) |
| **Balanced** | ~10.7% | -10.6% | Optimized mix of SBN and Base Yields |
| **Max Yield** | ~18.9% | -14.6% | High allocation to Pendle YT/PT within caps |

## 🏗️ Technical Architecture

```text
.
├── data
│   ├── raw           # Input data (SBN, USD/IDR, MMF NAV, DeFiLlama)
│   └── processed     # Unified yields, blended covariance, and frontier data
├── notebooks         # Execution Pipeline (00 to 05)
├── src               # Core Logic (Risk adjustment, Normalization, Optimizer)
├── scripts           # Robust standalone execution scripts
└── requirements.txt  # Project dependencies
```

### The Pipeline
1. **Research**: Fetch live DeFi data and define security/liquidity parameters.
2. **Normalization**: Convert all yields to annualized IDR terms.
3. **Risk Adjustment**: Apply empirical haircuts for protocol risks.
4. **Regime Modeling**: Classify market conditions and estimate blended covariance.
5. **Optimization**: Construct the Efficient Frontier.

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

### Running the Model
For a step-by-step walkthrough, run the notebooks in order:
```bash
# Or run the automation scripts
python3 scripts/process_normalization.py
python3 scripts/process_risk_adjustment.py
python3 scripts/process_covariance.py
python3 scripts/process_optimization.py
```

## 🛠️ Tech Stack
- **Optimization**: [CVXPY](https://www.cvxpy.org/) (SCS/Clarabel Solvers)
- **Data Handling**: Pandas, NumPy
- **API Integration**: DeFiLlama
- **Visualization**: Plotly

---
*Disclaimer: This is a sample model for institutional treasury research and does not constitute financial advice.*
