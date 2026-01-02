
"""
Enhanced DCF Valuation Engine - Institutional Grade
Prof. V. Ravichandran | The Mountain Path - World of Finance
Implements: WACC calculation, scenario analysis, risk metrics, detailed FCFF tracking

Key Improvements over Original:
1. Comprehensive WACC calculation with cost of debt & equity
2. Scenario analysis (Bull/Base/Bear cases)
3. Terminal value risk warnings
4. Enhanced FCFF component tracking
5. Interest coverage & financial health metrics
6. Logging for transparency & debugging
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scenario(Enum):
    """Valuation scenario definitions"""
    BEAR = "bear"
    BASE = "base"
    BULL = "bull"


@dataclass
class DCFConfig:
    """Centralized DCF model configuration"""
    FORECAST_YEARS: int = 5
    DEFAULT_TAX_RATE: float = 0.21
    DEFAULT_ROC: float = 0.15
    MAX_REINVESTMENT_RATE: float = 0.80
    TERMINAL_VALUE_WARNING_THRESHOLD: float = 0.70  # 70%
    MIN_INTEREST_COVERAGE_HEALTHY: float = 5.0
    MIN_INTEREST_COVERAGE_ACCEPTABLE: float = 1.5


@dataclass
class WACCComponents:
    """Detailed WACC breakdown"""
    cost_of_equity: float
    cost_of_debt: float
    equity_weight: float
    debt_weight: float
    beta: float
    interest_coverage: float
    credit_spread: float
    wacc: float


def calculate_wacc_detailed(inputs: Dict, 
                            risk_free_rate: float = 0.045, 
                            equity_risk_premium: float = 0.055) -> Tuple[float, WACCComponents]:
    """
    Calculate comprehensive Weighted Average Cost of Capital (WACC)
    
    WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)
    
    Where:
        E/V = Market value of equity / Total firm value
        D/V = Market value of debt / Total firm value
        Re = Cost of Equity = Rf + β × ERP + Size Premium + Company Premium
        Rd = Cost of Debt = Rf + Credit Spread
        Tc = Corporate tax rate
    
    Args:
        inputs: Dictionary with keys: current_price, shares, ebit, interest_exp, debt, tax_rate, beta
        risk_free_rate: Current risk-free rate (default 4.5%)
        equity_risk_premium: Equity risk premium (default 5.5%)
    
    Returns:
        Tuple: (WACC value, WACCComponents dataclass with breakdown)
    """
    
    logger.info("=" * 70)
    logger.info("WACC CALCULATION - DETAILED BREAKDOWN")
    logger.info("=" * 70)
    
    # --- COST OF EQUITY ---
    beta = inputs.get('beta', 1.0)
    
    # Market risk premium component
    market_risk_component = beta * equity_risk_premium
    
    # Size premium: negative for mega-cap companies (GOOGL, MSFT)
    market_cap = (inputs.get('current_price', 0) * inputs.get('shares', 1)) / 1e6
    if market_cap > 500_000:  # > $500B
        size_premium = 0.00
    elif market_cap > 100_000:  # > $100B
        size_premium = -0.002  # -20 bps
    elif market_cap > 10_000:  # > $10B
        size_premium = -0.005  # -50 bps
    else:
        size_premium = 0.010  # +100 bps for small cap
    
    # Company-specific premium for unsystematic risk
    company_specific_premium = 0.005  # 50 bps
    
    cost_of_equity = risk_free_rate + market_risk_component + size_premium + company_specific_premium
    
    logger.info(f"\nCOST OF EQUITY COMPONENTS:")
    logger.info(f"  Risk-Free Rate (Rf):           {risk_free_rate:7.2%}")
    logger.info(f"  Beta (β):                      {beta:7.2f}")
    logger.info(f"  Market Risk Premium (β×ERP):   {market_risk_component:7.2%}")
    logger.info(f"  Size Premium:                  {size_premium:7.2%}")
    logger.info(f"  Company-Specific Premium:      {company_specific_premium:7.2%}")
    logger.info(f"  ─────────────────────────────────────")
    logger.info(f"  Cost of Equity (Re):           {cost_of_equity:7.2%}")
    
    # --- COST OF DEBT ---
    ebit = inputs.get('ebit', 1)
    interest_exp = inputs.get('interest_exp', 0)
    
    # Calculate interest coverage ratio
    interest_coverage = ebit / (interest_exp + 1e-8)  # Avoid division by zero
    
    # Credit spread based on interest coverage (simplified rating approach)
    # Reference: Altman Z-Score and rating agency metrics
    if interest_coverage > 8:
        # AAA/AA equivalent
        credit_spread = 0.015  # 150 bps
        rating = "AAA/AA"
    elif interest_coverage > 5:
        # A equivalent
        credit_spread = 0.020  # 200 bps
        rating = "A"
    elif interest_coverage > 2.5:
        # BBB equivalent
        credit_spread = 0.030  # 300 bps
        rating = "BBB"
    elif interest_coverage > 1.5:
        # BB equivalent (high-yield)
        credit_spread = 0.050  # 500 bps
        rating = "BB"
    else:
        # B or lower (distressed)
        credit_spread = 0.080  # 800 bps
        rating = "B or Lower"
    
    cost_of_debt = risk_free_rate + credit_spread
    
    logger.info(f"\nCOST OF DEBT COMPONENTS:")
    logger.info(f"  Risk-Free Rate (Rf):           {risk_free_rate:7.2%}")
    logger.info(f"  Credit Spread (estimate):      {credit_spread:7.2%}")
    logger.info(f"  Implied Rating:                {rating:>7}")
    logger.info(f"  Interest Coverage Ratio:       {interest_coverage:7.2f}x")
    logger.info(f"  ─────────────────────────────────────")
    logger.info(f"  Cost of Debt (Rd):             {cost_of_debt:7.2%}")
    
    # --- CAPITAL STRUCTURE ---
    # Market values (not book values)
    equity_market_value = (inputs.get('current_price', 0) * inputs.get('shares', 1)) / 1e6
    debt_market_value = inputs.get('debt', 0)
    total_firm_value = equity_market_value + debt_market_value
    
    if total_firm_value == 0:
        logger.warning("Total firm value is zero - using equity value only")
        equity_weight = 1.0
        debt_weight = 0.0
    else:
        equity_weight = equity_market_value / total_firm_value
        debt_weight = debt_market_value / total_firm_value
    
    tax_rate = inputs.get('tax_rate', 0.21)
    
    logger.info(f"\nCAPITAL STRUCTURE (Market Values):")
    logger.info(f"  Equity Market Value:           ${equity_market_value:>10,.0f}M")
    logger.info(f"  Debt Market Value:             ${debt_market_value:>10,.0f}M")
    logger.info(f"  Total Firm Value:              ${total_firm_value:>10,.0f}M")
    logger.info(f"  Equity Weight (E/V):           {equity_weight:7.2%}")
    logger.info(f"  Debt Weight (D/V):             {debt_weight:7.2%}")
    logger.info(f"  Tax Rate (Tc):                 {tax_rate:7.2%}")
    
    # --- FINAL WACC ---
    wacc = (equity_weight * cost_of_equity + 
            debt_weight * cost_of_debt * (1 - tax_rate))
    
    logger.info(f"\nFINAL WACC CALCULATION:")
    logger.info(f"  WACC = (E/V)×Re + (D/V)×Rd×(1-Tc)")
    logger.info(f"       = {equity_weight:.3f}×{cost_of_equity:.3f} + {debt_weight:.3f}×{cost_of_debt:.3f}×{(1-tax_rate):.3f}")
    logger.info(f"       = {wacc:.2%}")
    logger.info("=" * 70)
    
    components = WACCComponents(
        cost_of_equity=cost_of_equity,
        cost_of_debt=cost_of_debt,
        equity_weight=equity_weight,
        debt_weight=debt_weight,
        beta=beta,
        interest_coverage=interest_coverage,
        credit_spread=credit_spread,
        wacc=wacc
    )
    
    return wacc, components


def run_multi_valuation_enhanced(inputs: Dict, 
                                growth_rate: float, 
                                wacc: float, 
                                t_growth: float, 
                                market_data: Dict) -> Dict:
    """
    Enhanced DCF valuation with detailed component tracking and risk metrics
    
    Two-Stage Model:
        Stage 1: Explicit 5-year forecast
        Stage 2: Terminal value (Gordon Growth Model)
    
    Args:
        inputs: Dictionary with revenue, ebit, tax_rate, shares, debt, cash, current_price
        growth_rate: Revenue growth rate (Stage 1, 5 years)
        wacc: Weighted Average Cost of Capital (discount rate)
        t_growth: Terminal growth rate (perpetuity)
        market_data: Dictionary with rf, erp
    
    Returns:
        Dictionary with valuation results and component breakdown
    """
    
    logger.info("\n" + "=" * 70)
    logger.info("DCF VALUATION - MULTI-STAGE MODEL")
    logger.info("=" * 70)
    
    # Extract inputs
    rev = inputs['revenue']
    ebit = inputs['ebit']
    tax_rate = inputs.get('tax_rate', DCFConfig.DEFAULT_TAX_RATE)
    shares_m = inputs['shares'] / 1e6
    
    logger.info(f"\nBASE YEAR FINANCIALS:")
    logger.info(f"  Revenue:                       ${rev:>10,.0f}M")
    logger.info(f"  EBIT:                          ${ebit:>10,.0f}M")
    logger.info(f"  EBIT Margin:                   {(ebit/rev)*100:>10.1f}%")
    logger.info(f"  Shares Outstanding:           {shares_m:>10,.1f}M")
    
    # Calculate ROC and reinvestment
    assumed_roc = inputs.get('roic', DCFConfig.DEFAULT_ROC)
    reinvestment_rate = min(growth_rate / assumed_roc, DCFConfig.MAX_REINVESTMENT_RATE)
    
    logger.info(f"\nREINVESTMENT ASSUMPTIONS:")
    logger.info(f"  Revenue Growth Rate:           {growth_rate:>10.2%}")
    logger.info(f"  Return on Capital (ROC):       {assumed_roc:>10.2%}")
    logger.info(f"  Implied Reinvestment Rate:     {reinvestment_rate:>10.2%}")
    logger.info(f"  Free Cash Flow Rate:           {(1-reinvestment_rate):>10.2%}")
    
    # === STAGE 1: EXPLICIT FORECAST (5 YEARS) ===
    projections = []
    current_rev = rev
    
    logger.info(f"\nSTAGE 1: EXPLICIT FORECAST (Years 1-5)")
    logger.info(f"{'Year':<6} {'Revenue':>12} {'EBIT':>12} {'NOPAT':>12} {'Reinvest':>12} {'FCFF':>12} {'PV Factor':>12} {'PV FCFF':>12}")
    logger.info("─" * 102)
    
    for year in range(1, DCFConfig.FORECAST_YEARS + 1):
        # Revenue projection
        current_rev *= (1 + growth_rate)
        
        # EBIT projection (constant margin assumption)
        year_ebit = current_rev * (ebit / rev) if rev > 0 else 0
        
        # NOPAT calculation
        year_nopat = year_ebit * (1 - tax_rate)
        
        # Reinvestment and FCFF
        reinvestment = year_nopat * reinvestment_rate
        fcff = year_nopat - reinvestment
        
        # Discount factor and PV
        pv_factor = 1 / ((1 + wacc) ** year)
        pv_fcff = fcff * pv_factor
        
        logger.info(f"{year:<6} ${current_rev:>11,.0f} ${year_ebit:>11,.0f} ${year_nopat:>11,.0f} "
                   f"${reinvestment:>11,.0f} ${fcff:>11,.0f} {pv_factor:>12.4f} ${pv_fcff:>11,.0f}")
        
        projections.append({
            'year': 2025 + year,
            'revenue': current_rev,
            'ebit': year_ebit,
            'tax_rate': tax_rate,
            'nopat': year_nopat,
            'reinvestment_rate': reinvestment_rate,
            'reinvestment': reinvestment,
            'fcff': fcff,
            'pv_factor': pv_factor,
            'pv_fcff': pv_fcff
        })
    
    df_projections = pd.DataFrame(projections)
    pv_fcff_explicit = df_projections['pv_fcff'].sum()
    
    # === STAGE 2: TERMINAL VALUE ===
    last_fcff = projections[-1]['fcff']
    
    # Safety check: WACC must exceed terminal growth
    stable_wacc = max(wacc, t_growth + 0.01)
    
    if stable_wacc <= t_growth:
        logger.error(f"TERMINAL VALUE ERROR: WACC ({stable_wacc:.2%}) <= Growth Rate ({t_growth:.2%})")
        raise ValueError(f"Invalid terminal value parameters: WACC must exceed terminal growth rate")
    
    # Gordon Growth Model
    terminal_value = (last_fcff * (1 + t_growth)) / (stable_wacc - t_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** DCFConfig.FORECAST_YEARS)  # CORRECT: use original WACC
    
    logger.info(f"\nSTAGE 2: TERMINAL VALUE (Gordon Growth Model)")
    logger.info(f"  Terminal Growth Rate (g):      {t_growth:>10.2%}")
    logger.info(f"  Year 5 FCFF:                   ${last_fcff:>10,.0f}M")
    logger.info(f"  Terminal Value Formula:        FCFF₅ × (1+g) / (WACC-g)")
    logger.info(f"  Terminal Value:                ${terminal_value:>10,.0f}M")
    logger.info(f"  PV of Terminal Value:          ${pv_terminal:>10,.0f}M")
    
    # === ENTERPRISE VALUE ===
    ev_m = pv_fcff_explicit + pv_terminal
    
    logger.info(f"\nENTERPRISE VALUE BRIDGE:")
    logger.info(f"  PV of Explicit Period FCFF:    ${pv_fcff_explicit:>10,.0f}M")
    logger.info(f"  PV of Terminal Value:          ${pv_terminal:>10,.0f}M")
    logger.info(f"  ─────────────────────────────────")
    logger.info(f"  Enterprise Value (EV):         ${ev_m:>10,.0f}M")
    
    # Terminal value as percentage of EV
    terminal_pct = (pv_terminal / ev_m) * 100
    
    # Risk warning for terminal value concentration
    if terminal_pct > DCFConfig.TERMINAL_VALUE_WARNING_THRESHOLD * 100:
        logger.warning(f"⚠️  TERMINAL VALUE RISK: {terminal_pct:.1f}% of EV")
        logger.warning(f"    Model is highly sensitive to long-term assumptions")
    
    # === EQUITY VALUE ===
    debt = inputs.get('debt', 0)
    cash = inputs.get('cash', 0)
    equity_val_m = ev_m - debt + cash
    
    logger.info(f"\nEQUITY VALUE BRIDGE:")
    logger.info(f"  Enterprise Value:              ${ev_m:>10,.0f}M")
    logger.info(f"  Less: Net Debt (D - C):        ${(debt - cash):>10,.0f}M")
    logger.info(f"  ─────────────────────────────────")
    logger.info(f"  Equity Value:                  ${equity_val_m:>10,.0f}M")
    
    # === FAIR VALUE PER SHARE ===
    price_dcf = equity_val_m / shares_m if shares_m > 0 else 0
    
    logger.info(f"\nFAIR VALUE CALCULATION:")
    logger.info(f"  Equity Value:                  ${equity_val_m:>10,.0f}M")
    logger.info(f"  Shares Outstanding:           {shares_m:>10,.1f}M")
    logger.info(f"  ─────────────────────────────────")
    logger.info(f"  Fair Value Per Share (DCF):    ${price_dcf:>10.2f}")
    
    # === RELATIVE VALUATION (P/E) ===
    net_income = inputs.get('net_income', 0)
    eps = net_income / shares_m if shares_m > 0 else 0
    pe_multiple = 15  # Conservative multiple
    price_pe = eps * pe_multiple
    
    logger.info(f"\nRELATIVE VALUATION (P/E Method):")
    logger.info(f"  Earnings Per Share (EPS):      ${eps:>10.2f}")
    logger.info(f"  Applied P/E Multiple:          {pe_multiple:>10.0f}x")
    logger.info(f"  Implied Price (P/E):           ${price_pe:>10.2f}")
    
    # === INVESTMENT METRICS ===
    current_price = inputs.get('current_price', 0)
    upside_pct = ((price_dcf - current_price) / current_price * 100) if current_price > 0 else 0
    mos = ((price_dcf - current_price) / price_dcf * 100) if price_dcf > 0 else 0
    
    logger.info(f"\nINVESTMENT METRICS:")
    logger.info(f"  Current Market Price:          ${current_price:>10.2f}")
    logger.info(f"  DCF Fair Value:                ${price_dcf:>10.2f}")
    logger.info(f"  Upside/(Downside):             {upside_pct:>10.1f}%")
    logger.info(f"  Margin of Safety:              {mos:>10.1f}%")
    logger.info("=" * 70 + "\n")
    
    return {
        'df': df_projections,
        'dcf_price': price_dcf,
        'pe_price': price_pe,
        'ev': ev_m,
        'equity_value': equity_val_m,
        'pv_explicit': pv_fcff_explicit,
        'pv_terminal': pv_terminal,
        'terminal_pct': terminal_pct,
        'current_price': current_price,
        'shares_m': shares_m,
        'upside_pct': upside_pct,
        'margin_of_safety': mos,
        'wacc_input': wacc
    }


def scenario_valuation(inputs: Dict, 
                      market_data: Dict,
                      rf: float = 0.045,
                      erp: float = 0.055) -> Dict:
    """
    Multi-scenario valuation: Bull, Base, Bear cases
    
    Allows risk assessment across different economic scenarios
    
    Returns:
        Dictionary with prices for each scenario
    """
    
    logger.info("\n" + "=" * 70)
    logger.info("SCENARIO ANALYSIS: BULL / BASE / BEAR CASES")
    logger.info("=" * 70)
    
    scenarios = {
        'bear': {
            'growth': 0.08,
            'wacc': 0.090,
            't_growth': 0.015,
            'description': 'Recession/Market Weakness'
        },
        'base': {
            'growth': 0.15,
            'wacc': 0.075,
            't_growth': 0.025,
            'description': 'Normal Economic Cycle'
        },
        'bull': {
            'growth': 0.20,
            'wacc': 0.065,
            't_growth': 0.030,
            'description': 'Expansion/Strong Growth'
        }
    }
    
    results = {}
    
    for scenario_name, scenario_params in scenarios.items():
        logger.info(f"\n{scenario_name.upper()} CASE: {scenario_params['description']}")
        logger.info(f"  Growth Rate: {scenario_params['growth']:.1%}, WACC: {scenario_params['wacc']:.2%}, Terminal G: {scenario_params['t_growth']:.2%}")
        
        result = run_multi_valuation_enhanced(
            inputs=inputs,
            growth_rate=scenario_params['growth'],
            wacc=scenario_params['wacc'],
            t_growth=scenario_params['t_growth'],
            market_data=market_data
        )
        
        results[scenario_name] = {
            'price': result['dcf_price'],
            'ev': result['ev'],
            'upside_pct': result['upside_pct'],
            'growth_rate': scenario_params['growth'],
            'wacc': scenario_params['wacc'],
            't_growth': scenario_params['t_growth']
        }
        
        logger.info(f"  → Fair Value: ${result['dcf_price']:.2f} ({result['upside_pct']:+.1f}% vs current)")
    
    logger.info("\n" + "=" * 70)
    
    return results


def sensitivity_heatmap_prices(inputs: Dict,
                               growth_rate: float,
                               wacc: float,
                               t_growth: float,
                               wacc_range: np.ndarray,
                               tg_range: np.ndarray,
                               market_data: Dict) -> np.ndarray:
    """
    Generate sensitivity matrix: DCF price across WACC and Terminal Growth ranges
    
    Args:
        wacc_range: Array of WACC values to test
        tg_range: Array of terminal growth values to test
    
    Returns:
        2D numpy array of prices (rows: WACC, cols: Terminal Growth)
    """
    
    matrix = np.full((len(wacc_range), len(tg_range)), np.nan)
    
    logger.info(f"Computing sensitivity matrix ({len(wacc_range)}×{len(tg_range)} scenarios)...")
    
    for i, w in enumerate(wacc_range):
        for j, g in enumerate(tg_range):
            if w <= g:
                # Invalid: WACC must exceed terminal growth
                matrix[i, j] = np.nan
            else:
                try:
                    result = run_multi_valuation_enhanced(
                        inputs, growth_rate, w, g, market_data
                    )
                    matrix[i, j] = result['dcf_price']
                except Exception as e:
                    logger.warning(f"Sensitivity calc failed for WACC={w:.2%}, TG={g:.2%}: {e}")
                    matrix[i, j] = np.nan
    
    logger.info("Sensitivity matrix computation complete")
    return matrix


# Example usage
if __name__ == "__main__":
    
    # Sample inputs (as if from SEC 10-K)
    sample_inputs = {
        'revenue': 280_000,      # Alphabet 2023 revenue ~$280B
        'ebit': 80_000,          # ~28.5% EBIT margin
        'net_income': 59_000,
        'tax_rate': 0.21,
        'shares': 12_700e6,      # ~12.7B shares
        'debt': 13_000,          # ~$13B
        'cash': 110_000,         # ~$110B
        'current_price': 140,    # Example price
        'interest_exp': 300,
        'beta': 0.95,
        'roic': 0.18
    }
    
    market_data = {
        'rf': 0.045,
        'erp': 0.055
    }
    
    # Calculate enhanced WACC
    wacc_calc, wacc_comp = calculate_wacc_detailed(sample_inputs)
    
    # Run enhanced valuation
    result = run_multi_valuation_enhanced(
        inputs=sample_inputs,
        growth_rate=0.15,
        wacc=wacc_calc,
        t_growth=0.025,
        market_data=market_data
    )
    
    print(f"\n✓ DCF Fair Value: ${result['dcf_price']:.2f}")
    print(f"✓ Current Price:  ${sample_inputs['current_price']:.2f}")
    print(f"✓ Upside:         {result['upside_pct']:+.1f}%")
    
    # Scenario analysis
    scenarios = scenario_valuation(sample_inputs, market_data)
    
    print("\n\nSCENARIO SUMMARY:")
    print(f"  Bear:  ${scenarios['bear']['price']:>8.2f} ({scenarios['bear']['upside_pct']:>+6.1f}%)")
    print(f"  Base:  ${scenarios['base']['price']:>8.2f} ({scenarios['base']['upside_pct']:>+6.1f}%)")
    print(f"  Bull:  ${scenarios['bull']['price']:>8.2f} ({scenarios['bull']['upside_pct']:>+6.1f}%)")
