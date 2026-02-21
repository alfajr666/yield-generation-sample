import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')
import normalization as norm

os.makedirs('data/processed', exist_ok=True)

def clean_val(x):
    if isinstance(x, str):
        return float(x.replace(',', ''))
    return x

# 1. Load USD/IDR
fx = pd.read_csv('data/raw/usd_idr_rate.csv')
fx['date'] = pd.to_datetime(fx['Date']).dt.strftime('%Y-%m-%d')
fx['usd_idr_rate'] = fx['Price'].apply(clean_val)
fx = fx[['date', 'usd_idr_rate']].sort_values('date')

# 2. Load SBN
sbn = pd.read_csv('data/raw/sbn_yields.csv')
sbn['date'] = pd.to_datetime(sbn['Date']).dt.strftime('%Y-%m-%d')
sbn['yield_annual'] = sbn['Price'].apply(clean_val) / 100.0
sbn['instrument'] = 'sbn'
sbn_f = sbn[['date', 'instrument', 'yield_annual']].copy()
sbn_f['yield_idr'] = sbn_f['yield_annual']

# 3. Load RDPU (MMF)
rdpu = pd.read_csv('data/raw/rdpu_nav.csv')
rdpu['date'] = pd.to_datetime(rdpu['date'])
rdpu = rdpu.set_index('date').resample('D').interpolate(method='linear')
# Use the function from normalization.py
rdpu['yield_annual'] = norm.annualize_nav_series(rdpu['nav'], window=30)
rdpu_f = rdpu.reset_index().rename(columns={'index':'date'})
rdpu_f['date'] = rdpu_f['date'].dt.strftime('%Y-%m-%d')
rdpu_f['instrument'] = 'mmf'
rdpu_f = rdpu_f[['date', 'instrument', 'yield_annual']].dropna().copy()
rdpu_f['yield_idr'] = rdpu_f['yield_annual']

# 4. Load On-Chain
aave = pd.read_csv('data/raw/aave_apy.csv', comment='#')
pt = pd.read_csv('data/raw/pendle_pt_apy.csv', comment='#')
yt = pd.read_csv('data/raw/pendle_yt_apy.csv', comment='#')

def process_on_chain(df, label):
    m = df.merge(fx, on='date', how='inner').sort_values('date')
    # Use 30-day rolling for FX adjustment to match MMF horizon
    m['fx_ret'] = (m['usd_idr_rate'] / m['usd_idr_rate'].shift(30))**(365/30) - 1
    m['yield_idr'] = (1 + m['yield_annual']) * (1 + m['fx_ret'].fillna(0)) - 1
    m['instrument'] = label
    return m[['date', 'instrument', 'yield_annual', 'yield_idr']]

aave_p = process_on_chain(aave, 'aave')
pt_p = process_on_chain(pt, 'pendle_pt')
yt_p = process_on_chain(yt, 'pendle_yt')

# 5. Combine and Save
master = pd.concat([sbn_f, rdpu_f, aave_p, pt_p, yt_p])
master.to_csv('data/processed/expected_returns.csv', index=False)

summary = master.groupby('instrument')['yield_idr'].mean()
summary.to_csv('data/processed/expected_returns_summary.csv')

print("Expected returns processed successfully.")
print(summary)
