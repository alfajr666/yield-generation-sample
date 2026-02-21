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
    Fallback if stress data is insufficient: assumes high correlation among crypto assets.
    """
    vols = np.sqrt(np.diag(cov_normal))
    # Correlation matrix:
    # 0: mmf, 1: sbn, 2: aave, 3: pendle_pt, 4: pendle_yt
    n = len(vols)
    corr_stress = np.eye(n)
    
    # Set on-chain/on-chain correlations to 0.85 (indices 2, 3, 4)
    crypto_indices = [2, 3, 4]
    for i in crypto_indices:
        for j in crypto_indices:
            if i != j:
                corr_stress[i, j] = 0.85
                
    # Set on-chain/off-chain correlations to -0.10
    offchain_indices = [0, 1]
    for i in crypto_indices:
        for j in offchain_indices:
            corr_stress[i, j] = -0.10
            corr_stress[j, i] = -0.10
            
    # Reconstruct covariance: V * Corr * V
    stress_cov = np.outer(vols, vols) * corr_stress
    return pd.DataFrame(stress_cov, index=cov_normal.index, columns=cov_normal.columns)
