
import pandas as pd
import numpy as np

def run_multi_valuation(inputs, growth_rate, wacc, t_growth, market_data):
    """Stabilized Engine using NOPAT-based Reinvestment"""
    rev = inputs['revenue']
    ebit = inputs['ebit']
    tax_rate = inputs.get('tax_rate', 0.21)
    
    # Fundamental Finance: We assume a 15% Return on Capital (ROC)
    # This prevents 'runaway' CapEx from breaking the model.
    assumed_roc = 0.15 
    reinvestment_rate = min(growth_rate / assumed_roc, 0.80) 

    projections = []
    for i in range(5):
        rev *= (1 + growth_rate)
        year_ebit = rev * (ebit / inputs['revenue']) if inputs['revenue'] > 0 else 0
        year_nopat = year_ebit * (1 - tax_rate)
        
        # FCFF = Cash left over after necessary growth reinvestment
        fcff = year_nopat * (1 - reinvestment_rate)
        pv = fcff / (1 + wacc)**(i + 1)
        
        projections.append({'Year': 2026+i, 'Revenue': rev, 'FCFF': fcff, 'PV_FCFF': pv})
    
    df = pd.DataFrame(projections)
    
    # Terminal Value Guard
    stable_wacc = max(wacc, t_growth + 0.01)
    terminal_value = (projections[-1]['FCFF'] * (1 + t_growth)) / (stable_wacc - t_growth)
    pv_terminal = terminal_value / (1 + stable_wacc)**5
    
    ev = df['PV_FCFF'].sum() + pv_terminal
    equity_value = ev - inputs['debt'] + inputs['cash']
    price_dcf = (equity_value * 1e6) / inputs['shares'] if inputs['shares'] > 0 else 0

    # Relative Valuations
    eps = (inputs['net_income'] / inputs['shares']) * 1e6 if inputs['shares'] > 0 else 0
    price_pe = eps * 15 # Conservative 15x Multiple

    return {
        "df": df, "dcf_price": price_dcf, "pe_price": price_pe,
        "ev": ev, "pv_terminal": pv_terminal, 
        "current_price": inputs['current_price'], "ddm_price": 0 # Placeholder
    }
