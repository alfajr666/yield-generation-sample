import sys
import os
import pandas as pd
import json

# Add src to path
sys.path.insert(0, 'src')
import risk_adjustment as risk
import utils

os.makedirs('data/processed', exist_ok=True)

# 1. Load Data
master = pd.read_csv('data/processed/expected_returns.csv')
params = utils.load_protocol_params('data/processed/protocol_params.json')

# 2. Get Mean Yields
summ = master.groupby('instrument')['yield_idr'].mean().reset_index()

# 3. Apply Haircuts
results = []
for _, row in summ.iterrows():
    inst = row['instrument']
    p_s = params[inst]
    mean_y = row['yield_idr']
    
    # Haircut 1: Exploit
    y_exp = risk.apply_exploit_haircut(mean_y, p_s['p'], p_s['s'])
    # Haircut 2: Liquidity
    y_final = risk.apply_liquidity_haircut(y_exp, p_s['liquidity_score'])
    
    results.append({
        'instrument': inst,
        'mean_yield_idr': mean_y,
        'expected_loss_haircut': p_s['p'] * p_s['s'],
        'risk_adjusted_yield_idr': y_final
    })

df = pd.DataFrame(results)
# Liquidity haircut is the residual
df['liquidity_haircut'] = df['mean_yield_idr'] - df['expected_loss_haircut'] - df['risk_adjusted_yield_idr']

# 4. Save
df.to_csv('data/processed/risk_adjusted_returns.csv', index=False)
print("Risk adjustments processed successfully.")
print(df)
