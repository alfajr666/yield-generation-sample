import sys
import os
import pandas as pd
import numpy as np
import cvxpy as cp
import json

# Add src to path
sys.path.insert(0, 'src')
import optimizer as opt

os.makedirs('data/processed', exist_ok=True)

# 1. Load Data
risk_adj = pd.read_csv('data/processed/risk_adjusted_returns.csv')
cov_df = pd.read_csv('data/processed/cov_blended.csv', index_col=0)

instruments = risk_adj['instrument'].tolist()
mu = risk_adj.set_index('instrument').loc[instruments, 'risk_adjusted_yield_idr'].to_numpy()
S = cov_df.loc[instruments, instruments].to_numpy()

hist = pd.read_csv('data/processed/expected_returns.csv')
pivot = hist.pivot(index='date', columns='instrument', values='yield_idr').reindex(columns=instruments).ffill().dropna()
scenarios = pivot.to_numpy()

# 3. Frontier (Constraints moved inside run_frontier for scoping safety)
frontier = opt.run_frontier(mu, S, scenarios, n_points=50)

if not frontier:
    print("FATAL: Frontier list is empty.")
    sys.exit(1)

df = pd.DataFrame(frontier)
for i, inst in enumerate(instruments):
    df[f'w_{inst}'] = df['weights'].apply(lambda x: x[i])

df.to_csv('data/processed/frontier_portfolios.csv', index=False)

# 4. Named
named = {
    "min_risk": df.iloc[0].to_dict(),
    "balanced": df.iloc[len(df)//2].to_dict(),
    "max_yield": df.iloc[-1].to_dict()
}
with open('data/processed/named_portfolios.json', 'w') as f:
    json.dump(named, f, indent=2)

print("Optimization complete.")
