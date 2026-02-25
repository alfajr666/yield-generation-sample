import requests
import pandas as pd
from datetime import datetime, timedelta
import os

def fetch_defillama_yields(protocol, days=365, symbol_filter=None):
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
    
    if symbol_filter:
        filtered_pools = [p for p in filtered_pools if symbol_filter in p['symbol']]
    
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

def fetch_pendle_yields_native(days=365):
    """
    Fetches PT and YT yield history from Pendle's native API.
    Returns (df_pt, df_yt).
    """
    chains = [1, 42161, 8453] # Main chains for Pendle stablecoins
    keywords = ['USDC', 'USDT', 'sUSDe']
    
    all_stable_markets = []
    for chainId in [1, 42161, 8453]:
        skip = 0
        limit = 100
        while True:
            url = f"https://api-v2.pendle.finance/core/v1/{chainId}/markets?limit={limit}&skip={skip}"
            r = requests.get(url)
            if r.status_code != 200:
                break
            data = r.json()
            markets = data.get('results', [])
            if not markets:
                break
            
            for m in markets:
                u_symbol = m.get('underlyingAsset', {}).get('symbol', '')
                a_symbol = m.get('accountingAsset', {}).get('symbol', '')
                search_text = (u_symbol + a_symbol + m.get('name', '')).lower()
                if any(k.lower() in search_text for k in keywords):
                    m['chainId'] = chainId
                    all_stable_markets.append(m)
            
            if len(markets) < limit:
                break
            skip += limit
                    
    if not all_stable_markets:
        raise ValueError("No stablecoin markets found on Pendle native API")
        
    # Pick the market with highest liquidity
    all_stable_markets.sort(key=lambda x: x.get('liquidity', {}).get('usd', 0), reverse=True)
    best_market = all_stable_markets[0]
    market_address = best_market['address']
    chainId = best_market['chainId']
    market_name = best_market['name']
    
    # Fetch History
    hist_url = f"https://api-v2.pendle.finance/core/v2/{chainId}/markets/{market_address}/history?time_frame=day"
    hist_r = requests.get(hist_url)
    hist_r.raise_for_status()
    hist_json = hist_r.json()
    hist_results = hist_json.get('results', [])
    
    if not hist_results:
        raise ValueError(f"No history found for Pendle market {market_address}")
        
    df = pd.DataFrame(hist_results)
    df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
    
    # PT DataFrame
    df_pt = df.copy()
    df_pt['yield_annual'] = df_pt['impliedApy']
    df_pt['instrument'] = 'pendle_pt'
    df_pt['currency'] = 'USD'
    df_pt['source'] = 'pendle_native'
    df_pt['notes'] = f"Market: {market_name} ({market_address}) on Chain {chainId}"
    
    # YT DataFrame
    df_yt = df.copy()
    # Note: Using ytFloatingApy as requested ("ytApy or equivalent")
    df_yt['yield_annual'] = df_yt['ytFloatingApy']
    df_yt['instrument'] = 'pendle_yt'
    df_yt['currency'] = 'USD'
    df_yt['source'] = 'pendle_native'
    df_yt['notes'] = f"Market: {market_name} ({market_address}) on Chain {chainId}"
    
    # Filter and slice
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    df_pt = df_pt[df_pt['date'] >= cutoff][['date', 'instrument', 'yield_annual', 'currency', 'source', 'notes']]
    df_yt = df_yt[df_yt['date'] >= cutoff][['date', 'instrument', 'yield_annual', 'currency', 'source', 'notes']]
    
    return df_pt, df_yt

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
    Uses absolute path relative to src/..
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    path = os.path.join(raw_dir, filename)
    fetch_date = datetime.now().strftime('%Y-%m-%d')
    
    with open(path, 'w') as f:
        f.write(f"# fetched: {fetch_date}\n")
        df.to_csv(f, index=False)
    print(f"Saved {filename} to {raw_dir}/")
