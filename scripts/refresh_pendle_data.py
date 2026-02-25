# scripts/refresh_pendle_data.py
import sys
import os
import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import data_fetch as dfetch

def refresh():
    print("Fetching Pendle yields from Native API...")
    try:
        df_pt, df_yt = dfetch.fetch_pendle_yields_native()
        dfetch.save_raw(df_pt, 'pendle_pt_apy.csv')
        dfetch.save_raw(df_yt, 'pendle_yt_apy.csv')
        
        print("\n--- Verification ---")
        print(f"PT mean APY: {df_pt['yield_annual'].mean()*100:.2f}%")
        print(f"YT mean APY: {df_yt['yield_annual'].mean()*100:.2f}%")
        print(f"Notes: {df_pt['notes'].iloc[0]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    refresh()
