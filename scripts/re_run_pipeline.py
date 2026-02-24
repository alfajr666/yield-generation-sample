import pandas as pd
import numpy as np
import json
import os
import sys
import cvxpy as cp

# Set root dir
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

import optimizer as opt
import risk_adjustment as risk
import utils

import covariance as cov

def run_step_02():
    print("Running Step 02: Risk Adjustment...")
    master_df = pd.read_csv(os.path.join(ROOT_DIR, 'data/processed/expected_returns.csv'))
    params = utils.load_protocol_params(os.path.join(ROOT_DIR, 'data/processed/protocol_params.json'))
    
    summary = master_df.groupby('instrument')['yield_idr'].mean().reset_index()
    
    adjusted_rows = []
    for inst in summary['instrument']:
        p_s = params[inst]
        mean_y = summary.loc[summary['instrument'] == inst, 'yield_idr'].iloc[0]
        
        y_exploit = risk.apply_exploit_haircut(mean_y, p_s['p'], p_s['s'])
        y_final = risk.apply_liquidity_haircut(y_exploit, p_s['liquidity_score'])
        
        adjusted_rows.append({
            'instrument': inst,
            'mean_yield_idr': mean_y,
            'expected_loss_haircut': p_s['p'] * p_s['s'],
            'risk_adjusted_yield_idr': y_final
        })
        
    risk_df = pd.DataFrame(adjusted_rows)
    risk_df['liquidity_haircut'] = risk_df['mean_yield_idr'] - risk_df['expected_loss_haircut'] - risk_df['risk_adjusted_yield_idr']
    
    # Fix 2: Sanity cap Pendle returns based on benchmarks
    if 'pendle_pt' in risk_df['instrument'].values:
        pt_mask = risk_df['instrument'] == 'pendle_pt'
        risk_df.loc[pt_mask, 'risk_adjusted_yield_idr'] = risk_df.loc[pt_mask, 'risk_adjusted_yield_idr'].clip(upper=0.14)
        print("Applied 14% sanity cap to Pendle PT.")
        
    if 'pendle_yt' in risk_df['instrument'].values:
        yt_mask = risk_df['instrument'] == 'pendle_yt'
        risk_df.loc[yt_mask, 'risk_adjusted_yield_idr'] = risk_df.loc[yt_mask, 'risk_adjusted_yield_idr'].clip(upper=0.18)
        print("Applied 18% sanity cap to Pendle YT.")
        
    output_path = os.path.join(ROOT_DIR, 'data/processed/risk_adjusted_returns.csv')
    risk_df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
    return risk_df

def run_step_03(risk_adj_df):
    print("Running Step 03: Covariance Calculation...")
    # Load historical returns to get normal covariance
    hist_returns = pd.read_csv(os.path.join(ROOT_DIR, 'data/processed/expected_returns.csv'))
    instruments = risk_adj_df['instrument'].tolist()
    pivot_hist = hist_returns.pivot(index='date', columns='instrument', values='yield_idr').reindex(columns=instruments).ffill().dropna()
    
    cov_normal = pivot_hist.cov()
    # Apply amplified stress assumption
    cov_stress = cov.construct_stress_covariance_assumption(cov_normal)
    # Blend (15% stress prob as per src/covariance.py default or explicit)
    cov_blended = cov.blend_covariance(cov_normal, cov_stress, stress_prob=0.15)
    
    cov_blended.to_csv(os.path.join(ROOT_DIR, 'data/processed/cov_blended.csv'))
    print("Blended covariance with amplified stress saved.")
    return cov_blended

def run_step_04(risk_adj_df):
    print("Running Step 04: CVaR Optimization...")
    cov_blended_df = pd.read_csv(os.path.join(ROOT_DIR, 'data/processed/cov_blended.csv'))
    if 'instrument' in cov_blended_df.columns:
        cov_blended_df = cov_blended_df.set_index('instrument')
    else:
        cov_blended_df.index = cov_blended_df.columns

    instruments = risk_adj_df['instrument'].tolist()
    mu = risk_adj_df.set_index('instrument').loc[instruments, 'risk_adjusted_yield_idr'].values
    S = cov_blended_df.loc[instruments, instruments].values

    # Step 4-extra: Generate Synthetic Scenarios from Blended Covariance
    print(f"Generating 30,000 synthetic scenarios from systemic blended covariance...")
    num_scenarios = 30000 
    returns_scenarios = np.random.multivariate_normal(mu, S, num_scenarios)

    # Run frontier with fixed optimizer
    frontier = opt.run_frontier(mu, S, [], returns_scenarios, n_points=100)
    
    frontier_df = pd.DataFrame(frontier)
    for i, inst in enumerate(instruments):
        frontier_df[f'w_{inst}'] = frontier_df['weights'].apply(lambda x: x[i])

    frontier_df.to_csv(os.path.join(ROOT_DIR, 'data/processed/frontier_portfolios.csv'), index=False)
    
    # Save named portfolios
    min_risk = frontier_df.iloc[0].to_dict()
    max_yield = frontier_df.iloc[-1].to_dict()
    balanced = frontier_df.iloc[len(frontier_df)//2].to_dict()

    named = {
        "min_risk": min_risk,
        "balanced": balanced,
        "max_yield": max_yield
    }

    with open(os.path.join(ROOT_DIR, 'data/processed/named_portfolios.json'), 'w') as f:
        json.dump(named, f, indent=2)
    
    print("Optimization complete. Portfolios saved.")
    return named

import generate_charts as viz

if __name__ == "__main__":
    risk_df = run_step_02()
    run_step_03(risk_df)
    named = run_step_04(risk_df)
    
    # Step 05: Visualization
    viz.run_visualization()
    
    print("\nSummary of results (Corrected Signs):")
    for name, p in named.items():
        print(f"{name.upper()}:")
        print(f"  Return: {p['expected_return']:.2%}")
        print(f"  CVaR: {p['cvar_95']:.2%}")
        # Find index of pendle_yt
        yt_idx = risk_df[risk_df['instrument'] == 'pendle_yt'].index[0]
        print(f"  YT Weight: {p['weights'][yt_idx]:.2%}")
