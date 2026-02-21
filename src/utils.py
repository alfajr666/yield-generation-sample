import pandas as pd
import json
import plotly.io as pio
import os

def validate_schema(df, required_columns):
    """
    Validates that a DataFrame contains the required columns.
    Raises ValueError if any column is missing.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def load_protocol_params(path='data/processed/protocol_params.json'):
    """
    Loads protocol parameters from a JSON file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Protocol params file not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def set_plotly_theme():
    """
    Sets a consistent visual theme for all Plotly charts.
    """
    pio.templates.default = "plotly_dark"
    # Custom color palette for the 5 instruments
    # mmf, sbn, aave, pendle_pt, pendle_yt
    colors = {
        'mmf': '#00CC96',       # Green
        'sbn': '#636EFA',       # Blue
        'aave': '#AB63FA',      # Purple
        'pendle_pt': '#FFA15A', # Orange
        'pendle_yt': '#EF553B'  # Red
    }
    return colors
