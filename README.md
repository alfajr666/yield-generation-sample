# 💰 Yield Generation & Optimization Model

**Portfolio Project by Gilang Fajar Wijayanto**  
Senior Treasury & Finance Operations Specialist | CFA Level I | FRM Part I  
[delomite.com](https://delomite.com) | [LinkedIn](https://www.linkedin.com/in/gilang-fajar-6973119a/)

---

## 📋 Overview

This repository demonstrates a production-grade yield optimization model designed for the treasury function of a regulated Indonesian crypto exchange (**Pedagang Aset Keuangan Digital** under OJK POJK No. 27 of 2024).

The model solves a specific, real problem: how should a crypto exchange treasury allocate its **own idle capital** — not customer funds, which are legally segregated — across a mix of traditional IDR instruments and on-chain USD protocols to maximize risk-adjusted return?

It features an **efficient frontier** built on CVaR optimization, incorporating two explicit risk layers that standard Markowitz ignores: smart contract exploit probability and liquidity heterogeneity.

**[Live Dashboard →](https://alfajr666.github.io/yield-generation-sample/dashboard/)**  
**[Detailed Analysis & Methodology →](https://delomite.com/blog/yield-generation-model/)**

### Business Context
Under **POJK No. 27 of 2024**, a licensed exchange must maintain minimum equity of Rp 50 billion. This model manages **own capital above the regulatory equity floor**, estimated at $2–5M for a newly licensed exchange. Stablecoins are classified as crypto assets, making on-chain deployment a deliberate, risk-governed decision.

### Key Features
- ✅ **Risk-Adjusted Yield (RAY)**: Applies explicit exploit and liquidity haircuts to raw yields.
- ✅ **Regime-Aware Covariance**: Blends normal and stress matrices (0.75 correlation floor during stress).
- ✅ **CVaR Optimization**: Minimizes 95% Expected Tail Loss using synthetic scenarios (CLARABEL solver).
- ✅ **Dynamic Instrument Exclusion**: Automatically filters instruments with negative risk-adjusted returns (e.g., Pendle YT in current compression).
- ✅ **Regulated Treasury Framework**: Strictly separates house money from consumer funds per OJK requirements.

---

## 📊 System Metrics (Current Market Baseline)

| Metric | Min Risk | Balanced | Max Yield |
|--------|----------|----------|-----------|
| **Expected Yield (IDR)** | 4.98% | 5.60% | 6.70% |
| **95% CVaR** | -3.35% (Gain) | -0.91% (Gain) | +4.17% (Loss) |
| **MMF + SBN Weight** | ~100% | ~82% | ~50% |
| **Aave Exposure** | 0% | ~18% | ~50% |
| **Pendle Exposure** | 0% | 0% | 0% |

### Instrument Universe
| ID | Instrument | Type | Currency | Status |
|----|------------|------|----------|--------|
| `mmf` | RDPU | Indonesian money market fund | IDR | Active |
| `sbn` | SBN < 1yr | Indonesian government bond | IDR | Active |
| `aave` | Aave USDC/USDT | On-chain lending | USD | Active |
| `pendle_pt` | Pendle PT | Fixed-rate DeFi yield | USD | Low spread |
| `pendle_yt` | Pendle YT | Leveraged floating yield | USD | Excluded (Negative) |

---

## 🗂️ Project Structure

```
yield-generation-model-sample/
├── data/
│   ├── raw/                        # User-sourced inputs (SBN, MMF, USD/IDR)
│   └── processed/                  # Pipeline outputs (Expected returns, Covariance)
│
├── notebooks/                      # Sequential execution pipeline
│   ├── 00_protocol_research.ipynb  # Data fetch (DeFiLlama/Pendle API)
│   ├── 01_data_normalization.ipynb # Yield to IDR conversion
│   ├── 02_risk_adjustment.ipynb    # RAY formula & haircuts
│   ├── 03_covariance_regime.ipynb  # Matrix blending
│   ├── 04_cvar_optimization.ipynb  # CVXPY CVaR frontier
│   └── 05_output_visualization.ipynb
│
├── src/                            # Core simulation & logic
│   ├── data_fetch.py               # API integrations (DeFiLlama + Pendle Native)
│   ├── normalization.py            # Yield conversion to IDR
│   ├── risk_adjustment.py          # RAY formula & return caps
│   ├── covariance.py               # Normal/Stress matrix logic
│   ├── optimizer.py                # CVXPY CVaR implementation
│   └── utils.py
│
├── scripts/                        # Automation & Research Utilities
│   ├── re_run_pipeline.py          # Single-command pipeline execution
│   ├── process_visualization.py    # Chart generation & export
│   └── research/                   # Granular DeFi/Pendle research scripts
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Installation
```bash
git clone https://github.com/alfajr666/yield-generation-model-sample.git
cd yield-generation-model-sample
pip install -r requirements.txt
```

### 2. Run Full Pipeline
```bash
python3 scripts/re_run_pipeline.py
```

### 3. Step-by-Step Execution
Open `notebooks/` and run `00` through `05` for granular execution with detailed commentary on the math and logic.

---

## 📈 Business Logic & Methodology

### Risk-Adjusted Yield (RAY)
All yields are normalized to IDR and adjusted via:
`RAY = Yield_Raw_IDR - (P_Exploit × S_Severity) - Liquidity_Haircut`
- **Exploit Haircut**: Derived from DeFiLlama history (Protocol age vs. Hacks).
- **Liquidity Haircut**: Based on Aave utilization and Pendle pool depth relative to a $3M exit size.

### Regime-Aware Optimization
The model blends a normal matrix with a **Stress Regime** matrix triggered by TVL drawdowns (>10-15%). Stress parameters include 3x vol amplification and a 0.75 correlation floor.

### CVaR Objective
Unlike variance optimization, CVaR focuses on the "worst-case" 5% tail. This is the institutional standard for a treasury that cannot afford capital impairment.

---

## 🎯 Use Cases
- **Treasury Managers**: Allocating house capital across IDR and DeFi benchmarks.
- **Risk Officers**: Quantifying smart contract and oracle risk in portfolio terms.
- **Compliance Teams**: Ensuring treasury activity stays within POJK 27/2024 equity bounds.
- **DeFi Strategists**: Analyzing yield spreads between PT/YT and off-chain anchors.

---

## ⚠️ Design Decisions & Limitations
- **Own Capital Only**: Strictly avoids customer funds to comply with Indonesian transparency laws.
- **Yield Compression**: Current model results reflect narrow spreads due to DeFi yield compression (Pendle YT currently negative). The framework is architected for reactivation when rates normalize.
- **Synthetic Dependency**: CVaR accuracy relies on the 30,000 synthetic scenarios sampled from the blended covariance.

---

## 🤝 Contact
**Gilang Fajar Wijayanto**  
Senior Treasury & Finance Operations Specialist  
📧 gilang.f@delomite.com  
🌐 [delomite.com](https://delomite.com)  
💼 [LinkedIn](https://www.linkedin.com/in/gilang-fajar-6973119a/)

**Certifications:**
- CFA Level I
- FRM Part I
- WMI & WPPE (OJK Indonesia)

---

**Built with:** Python, CVXPY, DeFiLlama API, Pendle API  
**Designed for:** Treasury Operations, Risk-Adjusted DeFi Deployment, Institutional Portfolio Management
