import numpy as np
import pandas as pd

def annualize_nav_series(nav_series, window=30):
    """
    Derives annualized yield from NAV appreciation over a rolling window.
    Formula: yield_annual = (nav_end / nav_start) ^ (365 / days) - 1
    """
    # Assuming daily data
    returns = nav_series.pct_change(window)
    # Annualize: (1 + r)^(365/window) - 1
    annualized = (1 + returns) ** (365 / window) - 1
    return annualized

def mean_reversion_blend(current, historical_mean, alpha=0.4):
    """
    Blends current spot rate with historical mean.
    Formula: 0.4 * current + 0.6 * historical_mean
    """
    return alpha * current + (1 - alpha) * historical_mean

def convert_usd_to_idr(yield_usd, fx_series):
    """
    Adjusts USD yield for FX return to get the IDR-denominated yield.
    Formula: yield_idr = (1 + yield_usd) * (1 + fx_return) - 1
    """
    # Assumes fx_series is daily USD/IDR rates matching the yield_usd frequency
    fx_return = fx_series.pct_change() # daily or window? window should match yield period
    # For daily yield series, we usually look at the FX change over the same horizon
    # But usually, this is applied to expected forward yield.
    # If the user provides a series, we use the corresponding period return.
    return (1 + yield_usd) * (1 + fx_return) - 1

def toggle_currency(df, direction='to_usd', fx_rate=None):
    """
    Applies or reverses FX conversion for the dashboard toggle.
    """
    if fx_rate is None:
        raise ValueError("FX rate is required for currency toggle")
        
    if direction == 'to_usd':
        # (1 + yield_idr) / (1 + fx_return) - 1 = yield_usd
        # This is a simplification.
        return (1 + df['yield_idr']) / (1 + fx_rate) - 1
    else:
        return (1 + df['yield_usd']) * (1 + fx_rate) - 1
