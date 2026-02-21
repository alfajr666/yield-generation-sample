import pandas as pd
import numpy as np

def apply_exploit_haircut(yield_series, p, s):
    """
    Applies haircut for protocol exploit expected loss.
    expected_loss = p * s
    """
    expected_loss = p * s
    return yield_series - expected_loss

def apply_liquidity_haircut(yield_series, liquidity_score):
    """
    Applies penalty based on liquidity score.
    """
    liquidity_penalty_map = {
        5: 0.0000,   # 0 bps
        4: 0.0005,   # 5 bps
        3: 0.0015,   # 15 bps
        2: 0.0030,   # 30 bps
        1: 0.0060,   # 60 bps
    }
    penalty = liquidity_penalty_map.get(liquidity_score, 0.0100) # Default to high penalty if score invalid
    return yield_series - penalty

def sensitivity_table(yield_series, p_range, s):
    """
    Generates a table of risk-adjusted yields across a range of p (probability).
    """
    results = {}
    for p in p_range:
        results[f"p_{p:.3f}"] = yield_series - (p * s)
    return pd.DataFrame(results)
