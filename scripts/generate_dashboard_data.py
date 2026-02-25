import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# Path Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
OUTPUT_FILE = os.path.join(DASHBOARD_DIR, "data.js")

# Constants
USD_IDR_RATE = 15700 # Default rate if not found elsewhere
BASE_CAPITAL_USD = 3000000
BASE_CAPITAL_IDR = BASE_CAPITAL_USD * USD_IDR_RATE
DAYS = 365
STRESS_EVENT_START = np.random.randint(180, 270)
STRESS_DURATION = 14
ON_CHAIN_INSTRUMENTS = ["aave", "pendle_pt", "pendle_yt"]
STRESS_SHOCK = -0.15

def generate_simulation(weights, expected_ann_return, cov_matrix, days=365):
    """
    Generates a 365-day cumulative return series using daily sampled returns.
    Includes a stress event.
    """
    # Daily parameters
    daily_return = expected_ann_return / 365
    daily_cov = cov_matrix / 365
    
    # Pre-allocate return array
    returns = np.zeros(days)
    
    # Portfolio variance
    portfolio_std = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights))) / np.sqrt(365)
    
    # Generate daily returns (simplified Monte Carlo)
    for d in range(days):
        # Base daily return with randomness
        r = np.random.normal(daily_return, portfolio_std)
        
        # Apply stress event shock
        if STRESS_EVENT_START <= d < STRESS_EVENT_START + STRESS_DURATION:
            # Check for on-chain exposure
            # Weights order: aave, mmf, pendle_pt, pendle_yt, sbn
            on_chain_weight = weights[0] + weights[2] + weights[3]
            # Extra daily shock applied to the on-chain portion
            r += (STRESS_SHOCK / STRESS_DURATION) * on_chain_weight
            
        returns[d] = r
    
    # Calculate cumulative value
    # We use (1+r) compounding for simplicity in dashboard visualization
    # Starting from 1.0 (multiplier)
    multiplier = 1.0
    series = []
    for d in range(days):
        multiplier *= (1 + returns[d])
        val_usd = BASE_CAPITAL_USD * multiplier
        val_idr = BASE_CAPITAL_IDR * multiplier
        series.append({
            "day": d + 1,
            "return_usd": round(val_usd, 2),
            "return_idr": round(val_idr, 2)
        })
    
    return series

def main():
    print("--- Starting Dashboard Data Generation ---")
    
    # 1. Load Data
    frontier_df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "frontier_portfolios.csv"))
    with open(os.path.join(PROCESSED_DATA_DIR, "named_portfolios.json"), 'r') as f:
        named_portfolios = json.load(f)
    cov_df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, "cov_blended.csv"), index_col=0)
    
    instruments = cov_df.columns.tolist()
    cov_matrix = cov_df.values
    
    # 2. Extract Frontier Data
    frontier_data = []
    for _, row in frontier_df.iterrows():
        frontier_data.append({
            "expected_return": float(row['expected_return']),
            "cvar": float(row['cvar_95'])
        })
    
    # 3. Process Named Portfolios
    processed_named = {}
    simulation_data = {}
    
    for key, data in named_portfolios.items():
        w = [data['w_aave'], data['w_mmf'], data['w_pendle_pt'], data['w_pendle_yt'], data['w_sbn']]
        processed_named[key] = {
            "expected_return": data['expected_return'],
            "cvar_95": data['cvar_95'],
            "weights": {
                "aave": data['w_aave'],
                "mmf": data['w_mmf'],
                "pendle_pt": data['w_pendle_pt'],
                "pendle_yt": data['w_pendle_yt'],
                "sbn": data['w_sbn']
            }
        }
        
        # 4. Generate Simulations
        print(f"Simulating {key} portfolio...")
        simulation_data[key] = generate_simulation(w, data['expected_return'], cov_matrix)

    # 5. Metadata
    meta = {
        "fetch_date": datetime.now().strftime("%Y-%m-%d"),
        "base_capital_usd": BASE_CAPITAL_USD,
        "base_capital_idr": BASE_CAPITAL_IDR,
        "usd_idr_rate": USD_IDR_RATE,
        "active_instruments": ["aave", "mmf", "pendle_pt", "sbn"],
        "excluded_instruments": [
            {"name": "pendle_yt", "reason": "Negative realized yield (-32% annualized)"}
        ]
    }
    
    stress_event = {
        "day": int(STRESS_EVENT_START),
        "label": "Simulated Stress Event",
        "duration_days": int(STRESS_DURATION)
    }

    # 6. Write JS constants
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)
        
    with open(OUTPUT_FILE, 'w') as f:
        f.write(f"const FRONTIER_DATA = {json.dumps(frontier_data)};\n\n")
        f.write(f"const NAMED_PORTFOLIOS = {json.dumps(processed_named)};\n\n")
        f.write(f"const SIMULATION_DATA = {json.dumps(simulation_data)};\n\n")
        f.write(f"const STRESS_EVENT = {json.dumps(stress_event)};\n\n")
        f.write(f"const META = {json.dumps(meta)};\n")

    print(f"Success! Dashboard data written to {OUTPUT_FILE}")
    print(f"Stress Day: {STRESS_EVENT_START}")

if __name__ == "__main__":
    main()
