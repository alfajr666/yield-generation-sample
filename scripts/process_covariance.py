import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, 'src')
import covariance as cov

os.makedirs('data/processed', exist_ok=True)

# 1. Prepare returns
master = pd.read_csv('data/processed/expected_returns.csv')
pivot = master.pivot(index='date', columns='instrument', values='yield_idr')
pivot = pivot.ffill().dropna()

# 2. Classify regimes
aave_tvl = pd.read_csv('data/raw/aave_tvl.csv', comment='#').drop_duplicates(subset=['date'])
pendle_tvl = pd.read_csv('data/raw/pendle_tvl.csv', comment='#').drop_duplicates(subset=['date'])

# Align TVL with returns
a_tvl = aave_tvl.set_index('date').reindex(pivot.index).ffill()
p_tvl = pendle_tvl.set_index('date').reindex(pivot.index).ffill()

regimes = cov.classify_regime(a_tvl['tvl_usd'], p_tvl['tvl_usd'])

# 3. Covariance
cov_normal = cov.estimate_covariance(pivot, regimes, 'normal')
cov_stress = cov.estimate_covariance(pivot, regimes, 'stress')

if (regimes == 'stress').sum() < 30:
    print(f"Stress days ({(regimes == 'stress').sum()}) < 30. Using assumed stress covariance.")
    cov_stress = cov.construct_stress_covariance_assumption(cov_normal)

cov_blended = cov.blend_covariance(cov_normal, cov_stress)

# 4. Save
cov_normal.to_csv('data/processed/cov_normal.csv')
cov_stress.to_csv('data/processed/cov_stress.csv')
cov_blended.to_csv('data/processed/cov_blended.csv')

print("Covariance matrices processed successfully.")
