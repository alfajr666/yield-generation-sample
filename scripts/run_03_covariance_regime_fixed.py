# run_03_covariance_regime_fixed.py
"""Execute the covariance and regime modeling step with duplicate handling.
This script replicates the logic of notebooks/03_covariance_regime.ipynb but ensures
that duplicate dates in the raw TVL files are removed before reindexing.
"""
import os
import pandas as pd
import numpy as np

# Add src to path for imports
import sys
sys.path.append(os.path.abspath('../src'))
import covariance as cov
import utils

# Load expected returns and pivot to wide format
returns_df = pd.read_csv('../data/processed/expected_returns.csv')
pivot_df = returns_df.pivot(index='date', columns='instrument', values='yield_idr')
pivot_df = pivot_df.ffill().dropna()

# Load TVL data
aave_tvl = pd.read_csv('../data/raw/aave_tvl.csv', comment='#')
pendle_tvl = pd.read_csv('../data/raw/pendle_tvl.csv', comment='#')

# Remove duplicate dates if any
if 'date' in aave_tvl.columns:
    aave_tvl = aave_tvl.drop_duplicates(subset='date')
if 'date' in pendle_tvl.columns:
    pendle_tvl = pendle_tvl.drop_duplicates(subset='date')

# Align dates with pivot_df
aave_tvl = aave_tvl.set_index('date').reindex(pivot_df.index).ffill()
pendle_tvl = pendle_tvl.set_index('date').reindex(pivot_df.index).ffill()

# Classify regimes
regimes = cov.classify_regime(aave_tvl['tvl_usd'], pendle_tvl['tvl_usd'])
print(f"Stress days found: {(regimes == 'stress').sum()}")

# Estimate covariance matrices
cov_normal = cov.estimate_covariance(pivot_df, regimes, 'normal')
cov_stress = cov.estimate_covariance(pivot_df, regimes, 'stress')

# If insufficient stress data, use synthetic assumption
if (regimes == 'stress').sum() < 30:
    print("Insufficient stress data. Using assumptions for stress covariance.")
    cov_stress = cov.construct_stress_covariance_assumption(cov_normal)

# Blend covariance
cov_blended = cov.blend_covariance(cov_normal, cov_stress, stress_prob=0.15)

# Save outputs
cov_normal.to_csv('../data/processed/cov_normal.csv')
cov_stress.to_csv('../data/processed/cov_stress.csv')
cov_blended.to_csv('../data/processed/cov_blended.csv')
print("Covariance matrices saved successfully.")
