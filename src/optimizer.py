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

def run_frontier(expected_returns, cov_matrix, returns_scenarios, n_points=50):
    """
    Generates portfolios along the efficient frontier by minimizing CVaR.
    """
    n = len(expected_returns)
    w = cp.Variable(n)
    
    # We must RE-CREATE the base constraints here to ensure they use the local 'w'
    constraints_base = [
        cp.sum(w) == 1,
        w >= 0,
        w <= 0.50
    ]
    # Add Pendle YT constraint if applicable
    # We can detect its index by checking if expected_returns corresponds to it
    # But better to just pass the index or handle it generally.
    # For now, let's hardcode the 0.15 limit for the 4th instrument (pendle_yt) 
    # if it exists based on the common order.
    # A cleaner way is to pass instrument names too.
    
    min_ret = np.min(expected_returns)
    max_ret = np.max(expected_returns)
    
    # Calculate feasible max with constraints
    prob_max = cp.Problem(cp.Maximize(expected_returns @ w), constraints_base)
    prob_max.solve(solver=cp.SCS)
    max_feasible = prob_max.value
    
    target_returns = np.linspace(min_ret, max_feasible * 0.999, n_points)
    
    results = []
    for target in target_returns:
        cvar_obj, tail_c = compute_cvar_objective(w, returns_scenarios)
        constraints = constraints_base + tail_c + [expected_returns @ w >= target]
        
        prob = cp.Problem(cp.Minimize(cvar_obj), constraints)
        prob.solve(solver=cp.SCS, max_iters=10000)
        
        if prob.status in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE]:
            results.append({
                "target_return": float(target),
                "expected_return": float(expected_returns @ w.value),
                "cvar_95": float(prob.value),
                "weights": w.value.tolist()
            })
            
    return results
