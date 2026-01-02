
import pandas as pd
import numpy as np

def run_dcf_engine(inputs, growth_rate, wacc, t_growth):
    """Calculates a 5-year Stage 1 projection and Stage 2 Terminal Value"""
    years = list(range(2026, 2031))
    projections = []
    
    # Starting values from latest 10-K
    rev = inputs['revenue']
    margin = inputs['ebit'] / inputs['revenue']
    tax_rate = min(inputs['tax_rate'], 0.30) # Capped at 30% for conservative modeling
    
    # Stage 1: 5-Year High Growth Period
    for i in range(5):
        rev *= (1 + growth_rate)
        ebit = rev * margin
        ebit_at = ebit * (1 - tax_rate)
        
        # FCFF = EBIT(1-t) + Depr - CapEx - ΔWC
        # Using a normalized 15% of Revenue for CapEx/WC reinvestment
        reinvestment = rev * 0.15 
        fcff = ebit_at - reinvestment + (inputs['depr'] * (rev/inputs['revenue']))
        
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
    last_fcff = projections[-1]['FCFF']
    terminal_value = (last_fcff * (1 + t_growth)) / (wacc - t_growth)
    pv_terminal_value = terminal_value / (1 + wacc) ** 5
    
    # Valuation Aggregation
    enterprise_value = df['PV_FCFF'].sum() + pv_terminal_value
    equity_value = enterprise_value - inputs['debt'] + inputs['cash']
    implied_price = (equity_value * 1e6) / inputs['shares']
    
    return df, enterprise_value, equity_value, implied_price

def calculate_sensitivity(inputs, growth_rate, wacc_range, g_range):
    """Generates an Enterprise Value matrix for sensitivity analysis"""
    matrix = np.zeros((len(wacc_range), len(g_range)))
    
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(g_range):
            # Ensure WACC > Growth to avoid division by zero in Gordon Growth
            if w <= g:
                matrix[i, j] = np.nan
            else:
                _, ev, _, _ = run_dcf_engine(inputs, growth_rate, w, g)
                matrix[i, j] = ev / 1000 # Convert to Billions for display
                
    return matrix
