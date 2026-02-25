import cvxpy as cp
import numpy as np
import pandas as pd

def compute_cvar_objective(weights, returns_scenarios, confidence=0.95):
    """
    Returns the CVaR objective expression for CVXPY.
    """
    num_scenarios = returns_scenarios.shape[0]
    zeta = cp.Variable()
    losses = -returns_scenarios @ weights
    tail_loss = cp.Variable(num_scenarios)
    constraints = [
        tail_loss >= 0,
        tail_loss >= losses - zeta
    ]
    cvar = zeta + (1 / (1 - confidence)) * cp.sum(tail_loss) / num_scenarios
    return cvar, constraints

def run_frontier(returns_df, cov_matrix_full, returns_scenarios_full, n_points=100):
    """
    Generates portfolios along the efficient frontier by minimizing CVaR.
    Filters out instruments with negative risk-adjusted returns.
    """
    # 1. Filter instruments with negative risk-adjusted returns
    # returns_df should have 'instrument' and 'risk_adjusted_yield_idr'
    active_mask = returns_df['risk_adjusted_yield_idr'] > 0
    active_df = returns_df[active_mask].copy()
    instruments = active_df['instrument'].tolist()
    
    print("Active instruments fed to optimizer:")
    print(active_df[['instrument', 'risk_adjusted_yield_idr']])
    
    if not instruments:
        print("Warning: No instruments with positive yield. Portfolio construction aborted.")
        return []

    # 2. Slice covariance and scenarios to match active instruments
    # Assumes cov_matrix_full index/columns match returns_df order or are instrument names
    if isinstance(cov_matrix_full, pd.DataFrame):
        S = cov_matrix_full.loc[instruments, instruments].values
    else:
        # Fallback to indexing if not a DataFrame (caller must ensure order)
        idx = returns_df.index[active_mask].tolist()
        S = cov_matrix_full[np.ix_(idx, idx)]

    if isinstance(returns_scenarios_full, pd.DataFrame):
        scenarios = returns_scenarios_full[instruments].values
    else:
        idx = returns_df.index[active_mask].tolist()
        scenarios = returns_scenarios_full[:, idx]

    mu = active_df['risk_adjusted_yield_idr'].values
    n = len(instruments)
    w = cp.Variable(n)

    # 3. Dynamic constraints based on instrument names
    inst_to_idx = {name: i for i, name in enumerate(instruments)}
    
    constraints_base = [
        cp.sum(w) == 1,
        w >= 0,
        w <= 0.50
    ]

    # Minimum 20% allocation to off-chain anchors (MMF + SBN)
    anchor_indices = [inst_to_idx[name] for name in ['mmf', 'sbn'] if name in inst_to_idx]
    if anchor_indices:
        constraints_base.append(cp.sum(w[anchor_indices]) >= 0.20)
    
    # 15% Cap on Pendle YT
    if 'pendle_yt' in inst_to_idx:
        constraints_base.append(w[inst_to_idx['pendle_yt']] <= 0.15)
    
    min_ret = np.min(mu)
    
    # Calculate feasible max with constraints
    prob_max = cp.Problem(cp.Maximize(mu @ w), constraints_base)
    try:
        prob_max.solve(solver=cp.CLARABEL)
    except:
        prob_max.solve(solver=cp.SCS)
    
    max_feasible = prob_max.value if prob_max.value is not None else np.max(mu)
    
    # Sweep from min to max feasible
    target_returns = np.linspace(min_ret, max_feasible * 0.999, n_points)
    
    results = []
    for target in target_returns:
        cvar_obj, tail_c = compute_cvar_objective(w, scenarios)
        constraints = constraints_base + tail_c + [mu @ w >= target]
        
        prob = cp.Problem(cp.Minimize(cvar_obj), constraints)
        try:
            prob.solve(solver=cp.CLARABEL)
        except:
            prob.solve(solver=cp.SCS, max_iters=10000)
        
        if prob.status in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
            # Map weights back to a consistent structure (all instruments from returns_df)
            full_weights = np.zeros(len(returns_df))
            for i, name in enumerate(instruments):
                orig_idx = returns_df[returns_df['instrument'] == name].index[0]
                full_weights[orig_idx] = w.value[i]

            results.append({
                "target_return": float(target),
                "expected_return": float(mu @ w.value),
                "cvar_95": float(prob.value),
                "weights": full_weights.tolist(),
                "active_instruments": instruments
            })
            
    return results
