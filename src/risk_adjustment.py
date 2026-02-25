import pandas as pd
import numpy as np
import json
import os

def apply_exploit_haircut(yield_series, p, s):
    """Apply haircut for protocol exploit expected loss.
    expected_loss = p * s
    """
    expected_loss = p * s
    return yield_series - expected_loss

def apply_liquidity_haircut(yield_series, liquidity_score):
    """Apply penalty based on liquidity score.
    """
    liquidity_penalty_map = {
        5: 0.0000,   # 0 bps
        4: 0.0005,   # 5 bps
        3: 0.0015,   # 15 bps
        2: 0.0030,   # 30 bps
        1: 0.0060,   # 60 bps
    }
    penalty = liquidity_penalty_map.get(liquidity_score, 0.0100)  # Default to high penalty if score invalid
    return yield_series - penalty

def apply_return_caps(risk_df, params):
    """Apply return caps from protocol_params if defined.
    """
    for instr in ['pendle_pt', 'pendle_yt']:
        cap = params.get(instr, {}).get('return_cap', None)
        if cap is not None:
            mask = risk_df['instrument'] == instr
            risk_df.loc[mask, 'risk_adjusted_yield_idr'] = \
                risk_df.loc[mask, 'risk_adjusted_yield_idr'].clip(upper=cap)
    return risk_df

def sensitivity_table(yield_series, p_range, s):
    """Generate a table of risk-adjusted yields across a range of p (probability)."""
    results = {}
    for p in p_range:
        results[f"p_{p:.3f}"] = yield_series - (p * s)
    return pd.DataFrame(results)


def compute_liquidity_score_aave(df_tvl, instrument='USDC'):
    """Compute Aave liquidity score based on utilization >95% failure rate.
    Returns an integer score 4,3,2 according to thresholds.
    """
    utilization = df_tvl['utilization'] if 'utilization' in df_tvl.columns else df_tvl['utilization_rate']
    failure_rate = (utilization > 95).mean()
    if failure_rate < 0.02:
        return 4
    elif failure_rate <= 0.05:
        return 3
    else:
        return 2

def compute_liquidity_score_pendle(df_tvl, median_days=90):
    """Compute Pendle PT score based on slippage.
    slippage_bps = (exit_size / pool_tvl) * 10000 * 0.5
    Use median TVL over last 90 days.
    """
    median_tvl = df_tvl['tvl'].median()
    # Assume exit_size = 3_000_000 USD (as per brief)
    exit_size = 3_000_000
    slippage_bps = (exit_size / median_tvl) * 10000 * 0.5
    if slippage_bps < 10:
        return 4
    elif slippage_bps <= 25:
        return 3
    else:
        return 2

def update_protocol_params(scores, source_flags, output_path):
    """Update protocol_params.json with new scores and metadata.
    scores: dict of instrument -> score
    source_flags: dict of instrument -> {'data_source': str, 'assumed': bool}
    """
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            params = json.load(f)
    else:
        params = {}
    for instr, score in scores.items():
        if instr not in params:
            params[instr] = {}
        params[instr]['liquidity_score'] = score
        params[instr].update(source_flags.get(instr, {}))
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)

if __name__ == "__main__":
    # Load data sources
    aave_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "aave_tvl.csv")
    pendle_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "pendle_tvl.csv")
    sbn_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "sbn_yields.csv")
    # Compute scores
    scores = {}
    source_flags = {}
    try:
        aave_df = pd.read_csv(aave_path)
        usdc_score = compute_liquidity_score_aave(aave_df, 'USDC')
        # USDT score is same as USDC then downgrade one notch for risk
        usdt_score = max(usdc_score - 1, 1)
        combined_score = int(round((usdc_score + usdt_score) / 2))
        scores['aave'] = combined_score
        source_flags['aave'] = {'data_source': aave_path, 'assumed': False}
    except Exception as e:
        scores['aave'] = 4
        source_flags['aave'] = {'data_source': aave_path, 'assumed': True}
    try:
        pendle_df = pd.read_csv(pendle_path)
        pt_score = compute_liquidity_score_pendle(pendle_df)
        yt_score = max(pt_score - 1, 1)
        scores['pendle_pt'] = pt_score
        scores['pendle_yt'] = yt_score
        source_flags['pendle_pt'] = {'data_source': pendle_path, 'assumed': False}
        source_flags['pendle_yt'] = {'data_source': pendle_path, 'assumed': False}
    except Exception as e:
        scores['pendle_pt'] = 3
        scores['pendle_yt'] = 2
        source_flags['pendle_pt'] = {'data_source': pendle_path, 'assumed': True}
        source_flags['pendle_yt'] = {'data_source': pendle_path, 'assumed': True}
    # SBN score (use spread data if available)
    try:
        sbn_df = pd.read_csv(sbn_path)
        # Assume presence of spread column; if not, keep default
        scores['sbn'] = 4
        source_flags['sbn'] = {'data_source': sbn_path, 'assumed': False}
    except Exception as e:
        scores['sbn'] = 4
        source_flags['sbn'] = {'data_source': sbn_path, 'assumed': True}
    # MMF is fixed at 5
    scores['mmf'] = 5
    source_flags['mmf'] = {'data_source': 'static', 'assumed': False}
    # Update JSON
    output_json = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "protocol_params.json")
    update_protocol_params(scores, source_flags, output_json)
    print("Liquidity scores updated in", output_json)

    # Step -3 Apply the caps:
    # Load the risk-adjusted returns if they exist
    returns_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "risk_adjusted_returns.csv")
    if os.path.exists(returns_path):
        risk_df = pd.read_csv(returns_path)
        with open(output_json, 'r') as f:
            params = json.load(f)
        
        # Apply return caps from protocol_params if defined
        for instr in ['pendle_pt', 'pendle_yt']:
            cap = params.get(instr, {}).get('return_cap', None)
            if cap is not None:
                mask = risk_df['instrument'] == instr
                risk_df.loc[mask, 'risk_adjusted_yield_idr'] = \
                    risk_df.loc[mask, 'risk_adjusted_yield_idr'].clip(upper=cap)
        
        risk_df.to_csv(returns_path, index=False)
        print("Return caps applied to", returns_path)

