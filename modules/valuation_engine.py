
import pandas as pd
import numpy as np

def run_multi_valuation(inputs, growth_rate, wacc, t_growth, market_data):
    """
    Institutional Multi-Method Valuation Engine
    Calculates: DCF (FCFF), DDM (Dividend Discount), and Relative P/E Valuation
    """
    
    # --- 1. DCF SECTION (Two-Stage Free Cash Flow to Firm) ---
    projection_years = 5
    rev = inputs['revenue']
    
    # Safety Check: EBIT Margin from audited data or industry floor
    margin = inputs['ebit'] / inputs['revenue'] if inputs['revenue'] > 0 else 0.15
    tax_rate = inputs.get('tax_rate', 0.21)
    
    projections = []
    for i in range(projection_years):
        # Projected Revenue Growth
        rev *= (1 + growth_rate)
        ebit = rev * margin
        tax_impact = ebit * (1 - tax_rate)
        
        # FCFF = EBIT(1-t) + Depr - CapEx
        # Scaling reinvestment based on revenue growth (Institutional Proxy)
        scaled_reinvestment = abs(inputs['capex']) * (rev / inputs['revenue']) if inputs['revenue'] > 0 else 0
        fcff = tax_impact + inputs['depr'] - scaled_reinvestment
        
        # Discounting to Present Value
        pv_factor = 1 / (1 + wacc)**(i + 1)
        pv_fcff = fcff * pv_factor
        
        projections.append({
            'Year': 2026 + i, 
            'Revenue': rev, 
            'FCFF': fcff, 
            'PV_FCFF': pv_fcff
        })
    
    df = pd.DataFrame(projections)
    
    # --- TERMINAL VALUE (Gordon Growth Method) ---
    # Safety Guard: WACC must be greater than terminal growth to avoid mathematical divergence
    if wacc <= t_growth:
        t_growth = wacc - 0.01
        
    last_fcff = projections[-1]['FCFF']
    terminal_value = (last_fcff * (1 + t_growth)) / (wacc - t_growth)
    pv_terminal_value = terminal_value / (1 + wacc)**projection_years
    
    # Enterprise Value (EV) = Sum(PV of Stage 1) + PV of Terminal Value
    ev = df['PV_FCFF'].sum() + pv_terminal_value
    
    # Equity Value = EV - Debt + Cash
    equity_dcf = ev - inputs['debt'] + inputs['cash']
    
    # Implied Price: (Equity Value $M * 1,000,000) / Absolute Shares
    price_dcf = (equity_dcf * 1e6) / inputs['shares'] if inputs['shares'] > 0 else 0

    # --- 2. DDM SECTION (Dividend Discount Model) ---
    # Cost of Equity (ke) via CAPM: Rf + (Beta * ERP)
    beta = inputs.get('beta', 1.1)
    ke = market_data['rf'] + (beta * market_data['erp'])
    
    # Dividends per share converted from $M to absolute $
    dps = (inputs['dividends'] / inputs['shares']) * 1e6 if inputs['shares'] > 0 else 0
    # Perpetual Dividend Growth Model
    price_ddm = (dps * (1 + 0.02)) / (ke - 0.02) if ke > 0.02 else 0

    # --- 3. P/E SECTION (Relative Valuation) ---
    # Earnings per share (EPS) converted from $M to absolute $
    eps = (inputs['net_income'] / inputs['shares']) * 1e6 if inputs['shares'] > 0 else 0
    price_pe = eps * 15 # baseline conservative P/E multiple

    return {
        "df": df,
        "dcf_price": price_dcf,
        "ddm_price": price_ddm,
        "pe_price": price_pe,
        "ev": ev,
        "pv_terminal": pv_terminal_value
    }

def calculate_sensitivity(inputs, growth_rate, wacc_range, g_range):
    """Generates an Enterprise Value matrix ($B) for heatmap visualization"""
    matrix = np.zeros((len(wacc_range), len(g_range)))
    market_data = {'rf': 0.045, 'erp': 0.055} 
    
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(g_range):
            if w <= g:
                matrix[i, j] = np.nan
            else:
                res = run_multi_valuation(inputs, growth_rate, w, g, market_data)
                # Return result in Billions for the UI Heatmap
                matrix[i, j] = res['ev'] / 1000 
                
    return matrix
