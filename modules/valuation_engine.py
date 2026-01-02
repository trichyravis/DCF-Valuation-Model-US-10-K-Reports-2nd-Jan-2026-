
import pandas as pd
import numpy as np

def run_dcf_engine(inputs, growth_rate, wacc, t_growth):
    """Calculates a 5-year Stage 1 projection and Stage 2 Terminal Value"""
    years = list(range(2026, 2031))
    projections = []
    
    # Starting values from audited SEC data
    rev = inputs['revenue']
    # Use Operating Income (EBIT) margin from the latest 10-K
    margin = inputs['ebit'] / inputs['revenue'] if inputs['revenue'] != 0 else 0
    tax_rate = min(inputs['tax_rate'], 0.30) # Capped for conservative modeling
    
    # Stage 1: 5-Year High Growth Period
    for i in range(5):
        rev *= (1 + growth_rate)
        ebit = rev * margin
        ebit_at = ebit * (1 - tax_rate)
        
        # FCFF Formula: EBIT(1-t) + Depr - CapEx - ΔWC
        # Normalized Reinvestment: 15% of Revenue (standard institutional proxy)
        reinvestment = rev * 0.15 
        # Scale depreciation with revenue growth
        scaled_depr = inputs['depr'] * (rev / inputs['revenue']) if inputs['revenue'] != 0 else 0
        
        fcff = ebit_at - reinvestment + scaled_depr
        
        pv_factor = 1 / (1 + wacc) ** (i + 1)
        pv_fcff = fcff * pv_factor
        
        projections.append({
            'Year': years[i],
            'Revenue': rev,
            'FCFF': fcff,
            'PV_FCFF': pv_fcff
        })

    df = pd.DataFrame(projections)
    
    # Stage 2: Terminal Value (Gordon Growth Method)
    # Safety Check: WACC must be greater than terminal growth
    if wacc <= t_growth:
        t_growth = wacc - 0.01 

    last_fcff = projections[-1]['FCFF']
    terminal_value = (last_fcff * (1 + t_growth)) / (wacc - t_growth)
    pv_terminal_value = terminal_value / (1 + wacc) ** 5
    
    # Valuation Aggregation (Results in Millions)
    enterprise_value = df['PV_FCFF'].sum() + pv_terminal_value
    # Equity Value = EV - Debt + Cash
    equity_value = enterprise_value - inputs['debt'] + inputs['cash']
    
    # Implied Price: (Equity Value in Millions * 1,000,000) / Shares Outstanding
    implied_price = (equity_value * 1e6) / inputs['shares'] if inputs['shares'] != 0 else 0
    
    return df, enterprise_value, equity_value, implied_price

def calculate_sensitivity(inputs, growth_rate, wacc_range, g_range):
    """Generates an Enterprise Value matrix (in Billions) for Heatmap visualization"""
    matrix = np.zeros((len(wacc_range), len(g_range)))
    
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(g_range):
            if w <= g:
                matrix[i, j] = np.nan
            else:
                _, ev, _, _ = run_dcf_engine(inputs, growth_rate, w, g)
                matrix[i, j] = ev / 1000 # Convert Millions to Billions for the Heatmap
                
    return matrix
