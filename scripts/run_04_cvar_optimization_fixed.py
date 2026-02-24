# run_04_cvar_optimization_fixed.py
"""Execute CVaR optimization steps originally in notebook 04.
This script loads required data, runs the frontier generation using the optimizer module,
and saves the frontier portfolios and named portfolios.
"""
import os
import sys
import pandas as pd
import json

# Ensure src is in path
sys.path.append(os.path.abspath('../src'))
import optimizer as opt

# Load data
risk_adj_path = '../data/processed/risk_adjusted_returns.csv'
cov_blended_path = '../data/processed/cov_blended.csv'
expected_returns_path = '../data/processed/expected_returns.csv'

risk_adj_df = pd.read_csv(risk_adj_path)
# Load cov_blended and set index if 'instrument' column exists
cov_blended_df = pd.read_csv(cov_blended_path)
if 'instrument' in cov_blended_df.columns:
    cov_blended_df = cov_blended_df.set_index('instrument')
else:
    cov_blended_df.index = cov_blended_df.columns

# Ensure order matches risk_adj_df
instruments = risk_adj_df['instrument'].tolist()
mu = risk_adj_df.set_index('instrument').loc[instruments, 'risk_adjusted_yield_idr'].values
S = cov_blended_df.loc[instruments, instruments].values

# Historical returns for scenarios
hist_returns = pd.read_csv('../data/processed/expected_returns.csv')
pivot_hist = hist_returns.pivot(index='date', columns='instrument', values='yield_idr')
# Align columns to instruments order, forward fill, drop NA
pivot_hist = pivot_hist.reindex(columns=instruments).ffill().dropna()
returns_scenarios = pivot_hist.values

# Run frontier generation
frontier = opt.run_frontier(mu, S, [], returns_scenarios, n_points=100)

# Convert results to DataFrame
frontier_df = pd.DataFrame(frontier)
# Add weight columns
for i, inst in enumerate(instruments):
    frontier_df[f'w_{inst}'] = frontier_df['weights'].apply(lambda x: x[i])

# Save frontier
frontier_df.to_csv('../data/processed/frontier_portfolios.csv', index=False)
print(f"Frontier saved with {len(frontier_df)} portfolios.")

# Named portfolios
min_risk = frontier_df.iloc[0].to_dict()
max_yield = frontier_df.iloc[-1].to_dict()
balanced = frontier_df.iloc[len(frontier_df)//2].to_dict()
named = {
    'min_risk': min_risk,
    'balanced': balanced,
    'max_yield': max_yield
}
with open('../data/processed/named_portfolios.json', 'w') as f:
    json.dump(named, f, indent=2)
print("Named portfolios saved.")
