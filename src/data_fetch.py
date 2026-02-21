import requests
import pandas as pd
from datetime import datetime, timedelta
import os

def fetch_defillama_yields(protocol, days=365):
    """
    Fetches yield history from DeFiLlama.
    Note: The 'pools' endpoint returns current state. 
    Historical yield for a pool requires the pool UUID.
    """
    # 1. Get all pools
    response = requests.get("https://yields.llama.fi/pools")
    response.raise_for_status()
    data = response.json()['data']
    
    # 2. Filter for protocol and stablecoins
    # Mapping protocol names to DeFiLlama slugs
    slug_map = {
        'aave': 'aave-v3',
        'pendle': 'pendle'
    }
    target_slug = slug_map.get(protocol, protocol)
    
    filtered_pools = [p for p in data if p['project'] == target_slug and p['stablecoin'] == True]
    
    # In a real scenario, we might pick the primary USDC pool
    # For this implementation, we fetch history for the largest USDC pool if available
    if not filtered_pools:
        raise ValueError(f"No stablecoin pools found for {protocol}")
        
    # Sort by TVL to get the most liquid one
    filtered_pools.sort(key=lambda x: x['tvlUsd'], reverse=True)
    pool_id = filtered_pools[0]['pool']
    
    # 3. Fetch history for the selected pool
    hist_response = requests.get(f"https://yields.llama.fi/chart/{pool_id}")
    hist_response.raise_for_status()
    hist_data = hist_response.json()['data']
    
    df = pd.DataFrame(hist_data)
    df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
    df['yield_annual'] = df['apy'] / 100.0
    df['instrument'] = protocol # will be mapped correctly in normalization
    df['currency'] = 'USD'
    df['source'] = 'defillama'
    df['notes'] = f"Pool: {filtered_pools[0]['symbol']} ({pool_id})"
    
    # Filter for last 365 days
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    df = df[df['date'] >= cutoff]
    
    return df[['date', 'instrument', 'yield_annual', 'currency', 'source', 'notes']]

def fetch_defillama_tvl(protocol, days=365):
    """
    Fetches TVL history.
    """
    response = requests.get(f"https://api.llama.fi/protocol/{protocol}")
    response.raise_for_status()
    data = response.json()
    
    tvl_history = data['tvl']
    df = pd.DataFrame(tvl_history)
    df['date'] = pd.to_datetime(df['date'], unit='s').dt.strftime('%Y-%m-%d')
    df.rename(columns={'totalLiquidityUSD': 'tvl_usd'}, inplace=True)
    
    # Filter for last 365 days
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    df = df[df['date'] >= cutoff]
    
    return df[['date', 'tvl_usd']]

def fetch_defillama_hacks():
    """
    Fetches all documented protocol exploits.
    """
    response = requests.get("https://api.llama.fi/hacks")
    response.raise_for_status()
    data = response.json()
    
    df = pd.DataFrame(data)
    # The hacks API might return a different structure, we'll keep it raw for now and filter in Notebook 00
    return df

def save_raw(df, filename):
    """
    Saves to data/raw/, prepends fetch date comment.
    """
    path = os.path.join('data/raw', filename)
    fetch_date = datetime.now().strftime('%Y-%m-%d')
    
    with open(path, 'w') as f:
        f.write(f"# fetched: {fetch_date}\n")
        df.to_csv(f, index=False)
    print(f"Saved {filename} to data/raw/")
