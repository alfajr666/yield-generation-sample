import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os

def run_visualization():
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(ROOT_DIR, 'data/processed/charts'), exist_ok=True)

    frontier_df = pd.read_csv(os.path.join(ROOT_DIR, 'data/processed/frontier_portfolios.csv'))
    with open(os.path.join(ROOT_DIR, 'data/processed/named_portfolios.json')) as f:
        named = json.load(f)

    print("Generating Efficient Frontier chart...")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frontier_df['cvar_95'],
        y=frontier_df['expected_return'],
        mode='lines+markers',
        name='Efficient Frontier (CVaR)',
        marker=dict(size=4)
    ))

    # Add named portfolios
    for name in ['min_risk', 'balanced', 'max_yield']:
        p = named[name]
        fig.add_trace(go.Scatter(
            x=[p['cvar_95']],
            y=[p['expected_return']],
            mode='markers+text',
            name=name.replace('_', ' ').capitalize(),
            text=[name.replace('_', ' ').capitalize()],
            textposition="top center",
            marker=dict(size=12, symbol='star')
        ))

    fig.update_layout(
        title='Efficient Frontier: Annualized Yield vs 95% CVaR',
        xaxis_title='95% CVaR (Expected Tail Loss)',
        yaxis_title='Annualized Risk-Adjusted Yield (IDR)',
        template='plotly_white'
    )
    # Ensure sign convention reflection in axis title
    fig.update_xaxes(title_text='95% CVaR (Positive = Loss, Negative = Gain)')
    
    fig.write_image(os.path.join(ROOT_DIR, 'data/processed/charts/efficient_frontier.png'))

    print("Generating Allocation Stack chart...")
    w_cols = [c for c in frontier_df.columns if c.startswith('w_')]
    
    # Rename columns for cleaner legend
    plot_df = frontier_df.copy()
    rename_dict = {c: c.replace('w_', '').upper() for c in w_cols}
    plot_df = plot_df.rename(columns=rename_dict)
    clean_w_cols = [rename_dict[c] for c in w_cols]

    fig2 = px.area(
        plot_df,
        x=np.arange(len(plot_df)),
        y=clean_w_cols,
        title='Portfolio Allocation vs Risk Level (Low Risk -> High Yield)',
        labels={'x': 'Portfolio Index', 'value': 'Weight'}
    )
    fig2.update_layout(template='plotly_white')
    fig2.write_image(os.path.join(ROOT_DIR, 'data/processed/charts/allocation_stack.png'))

    # Generate summary CSV
    summary_rows = []
    for name, p in named.items():
        row = {
            'portfolio': name,
            'yield': p['expected_return'],
            'cvar_95': p['cvar_95']
        }
        # Append weights
        for k, v in p.items():
            if k.startswith('w_'):
                row[k.replace('w_', '')] = v
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(ROOT_DIR, 'data/processed/final_summary.csv'), index=False)
    print("Charts and summary saved.")

if __name__ == "__main__":
    run_visualization()
