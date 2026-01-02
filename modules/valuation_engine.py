
import pandas as pd
import numpy as np


def run_multi_valuation(inputs, growth_rate, wacc, t_growth, market_data):
    """
    Institutional Valuation Logic
    
    INPUT ASSUMPTIONS (all from SEC):
    - revenue: in MILLIONS ($M)
    - ebit: in MILLIONS ($M)
    - debt: in MILLIONS ($M)
    - cash: in MILLIONS ($M)
    - shares: in MILLIONS (M shares) - CORRECTED
    
    OUTPUT:
    - Fair Value Per Share: in DOLLARS ($)
    - Enterprise Value: in MILLIONS ($M)
    """
    
    # --- 0. INPUT EXTRACTION & VALIDATION ---
    rev = inputs.get('revenue', 0)
    ebit = inputs.get('ebit', 0)
    shares_m = inputs.get('shares', 1)  # In millions
    current_price = inputs.get('current_price', 0)
    debt = inputs.get('debt', 0)
    cash = inputs.get('cash', 0)
    net_income = inputs.get('net_income', 0)
    
    # Validate
    if rev <= 0 or shares_m <= 0:
        return {
            "df": pd.DataFrame(),
            "dcf_price": 0,
            "pe_price": 0,
            "ev": 0,
            "pv_terminal": 0,
            "current_price": current_price,
            "ddm_price": 0
        }
    
    tax_rate = inputs.get('tax_rate', 0.21)
    
    # Reinvestment calculation
    assumed_roc = 0.15
    reinvestment_rate = min(max(growth_rate / assumed_roc, 0), 0.80) if assumed_roc > 0 else 0

    # --- 1. 5-YEAR PROJECTION (STAGE 1) ---
    projections = []
    current_rev = rev
    
    for i in range(5):
        current_rev *= (1 + growth_rate)
        
        # Use EBIT margin from base year
        ebit_margin = (ebit / rev) if rev > 0 else 0.10
        year_ebit = current_rev * ebit_margin
        year_nopat = year_ebit * (1 - tax_rate)
        
        # FCFF = NOPAT * (1 - Reinvestment Rate)
        fcff = year_nopat * (1 - reinvestment_rate)
        
        pv_factor = 1 / (1 + wacc)**(i + 1)
        pv_fcff = fcff * pv_factor
        
        projections.append({
            'Year': 2026 + i,
            'Revenue': current_rev,
            'FCFF': fcff,
            'PV_FCFF': pv_fcff
        })
    
    df = pd.DataFrame(projections)

    # --- 2. TERMINAL VALUE (STAGE 2) ---
    stable_wacc = max(wacc, t_growth + 0.01)
    last_fcff = projections[-1]['FCFF']
    
    if stable_wacc > t_growth:
        terminal_value = (last_fcff * (1 + t_growth)) / (stable_wacc - t_growth)
        pv_terminal = terminal_value / (1 + wacc)**5
    else:
        pv_terminal = 0
    
    # --- 3. ENTERPRISE VALUE (in $M) ---
    ev_m = df['PV_FCFF'].sum() + pv_terminal
    
    # --- 4. EQUITY VALUE BRIDGE (in $M) ---
    equity_val_m = ev_m - debt + cash
    
    # --- 5. FAIR VALUE PER SHARE (in $) ---
    # Fair Value = Equity Value ($M) / Shares (M shares) = $ per share
    price_dcf = equity_val_m / shares_m if shares_m > 0 else 0
    
    # --- 6. RELATIVE VALUATION (P/E method) ---
    eps = net_income / shares_m if shares_m > 0 else 0
    price_pe = eps * 15 if eps > 0 else 0

    return {
        "df": df,
        "dcf_price": price_dcf,
        "pe_price": price_pe,
        "ev": ev_m,
        "pv_terminal": pv_terminal,
        "current_price": current_price,
        "ddm_price": 0
    }


def calculate_sensitivity(inputs, growth_rate, wacc_range, g_range):
    """Generates Enterprise Value sensitivity matrix in Billions"""
    matrix = np.zeros((len(wacc_range), len(g_range)))
    market_data = {'rf': 0.045, 'erp': 0.055}
    
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(g_range):
            if w <= g:
                matrix[i, j] = np.nan
            else:
                res = run_multi_valuation(inputs, growth_rate, w, g, market_data)
                matrix[i, j] = res['ev'] / 1000 if res['ev'] > 0 else np.nan
                
    return matrix
