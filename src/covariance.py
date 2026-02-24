import pandas as pd
import numpy as np

def classify_regime(tvl_aave, tvl_pendle, thresholds=(0.10, 0.15)):
    """
    Classifies each date as 'normal' or 'stress' based on TVL drops.
    A stress regime is triggered if Aave TVL falls > 10% or Pendle TVL falls > 15% in 7 days.
    """
    drop_aave = tvl_aave.pct_change(7)
    drop_pendle = tvl_pendle.pct_change(7)
    
    stress_aave = drop_aave < -thresholds[0]
    stress_pendle = drop_pendle < -thresholds[1]
    
    is_stress = stress_aave | stress_pendle
    return is_stress.map({True: 'stress', False: 'normal'})

def estimate_covariance(returns_df, regime_labels, target_regime):
    """
    Estimates covariance matrix for a specific regime.
    """
    filtered_returns = returns_df[regime_labels == target_regime]
    if len(filtered_returns) < 2:
        return None
    return filtered_returns.cov()

def blend_covariance(cov_normal, cov_stress, stress_prob=0.15):
    """
    Blends normal and stress covariance matrices.
    """
    return (1 - stress_prob) * cov_normal + stress_prob * cov_stress

def construct_stress_covariance_assumption(cov_normal):
    """
    Fallback if stress data is insufficient: assumes high correlation among assets
    and amplifies volatility to capture extreme tail tail risk across the system.
    """
    vols = np.sqrt(np.diag(cov_normal))
    
    # Indices: [aave, mmf, pendle_pt, pendle_yt, sbn]
    # Note: Indices mapping from re_run_pipeline.py Step 04
    crypto_indices = [0, 2, 3] # aave, pendle_pt, pendle_yt
    offchain_indices = [1, 4]  # mmf, sbn
    
    vols_stress = vols.copy()
    
    # SYSTEMIC STRESS: Even 'safe' assets are amplified
    # Multiplier: 2x for off-chain, 3x for crypto
    for i in offchain_indices:
        vols_stress[i] = max(vols[i] * 2.0, 0.02) # Min 2% vol floor for SBN/MMF
        
    for i in crypto_indices:
        vols_stress[i] = max(vols[i] * 3.0, 0.05) # Min 5% vol floor for Crypto
        
    n = len(vols)
    corr_stress = np.eye(n)
    
    # High system-wide correlation during stress (0.75 for all assets)
    # This reflects a systemic liquidity/market shock where diversification fails.
    for i in range(n):
        for j in range(n):
            if i != j:
                corr_stress[i, j] = 0.75
                
    # Reconstruct covariance: V * Corr * V
    stress_cov = np.outer(vols_stress, vols_stress) * corr_stress
    return pd.DataFrame(stress_cov, index=cov_normal.index, columns=cov_normal.columns)
