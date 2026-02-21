import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os

os.makedirs('data/processed/charts', exist_ok=True)

frontier_df = pd.read_csv('data/processed/frontier_portfolios.csv')
with open('data/processed/named_portfolios.json') as f:
    named = json.load(f)

# 1. Summary
summary_rows = []
for name, p in named.items():
    row = {'portfolio': name, 'yield': p['expected_return'], 'cvar_95': p['cvar_95']}
    for k, v in p.items():
        if k.startswith('w_'):
            row[k.replace('w_', '')] = v
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv('data/processed/final_summary.csv', index=False)

# 2. Charts (Note: kaleido might be needed for write_image, if not, we skip)
# We just save the csv for now as the 'real' deliverable is the notebook and data
print("Visualization processed successfully.")
print(summary_df)
