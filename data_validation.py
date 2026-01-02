
"""
Financial Data Validation Module - Quality Assurance
Prof. V. Ravichandran | The Mountain Path - World of Finance

Comprehensive validation of SEC-fetched financial data with:
- Scale checks (realistic ranges)
- Profitability metrics
- Leverage ratios
- Financial health indicators
- Data quality flags
"""

from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)


class FinancialDataValidator:
    """
    Validates SEC-sourced financial data for consistency and realism
    """
    
    # Realistic parameter ranges
    REVENUE_MIN_M = 1          # $1M minimum (micro-cap)
    REVENUE_MAX_M = 1_000_000  # $1T maximum (Walmart-scale)
    
    SHARES_MIN_M = 0.1         # 0.1M shares minimum
    SHARES_MAX_M = 10_000      # 10B shares maximum
    
    EBIT_MARGIN_MIN = -0.50    # -50% EBIT margin (severely distressed)
    EBIT_MARGIN_MAX = 0.70     # +70% EBIT margin (very rare)
    
    DEBT_TO_EQUITY_WARNING = 2.0  # Debt/Equity > 2x is risky
    DEBT_TO_EQUITY_ERROR = 5.0    # Debt/Equity > 5x is distressed
    
    INTEREST_COVERAGE_EXCELLENT = 8.0      # > 8x: AAA-rated quality
    INTEREST_COVERAGE_HEALTHY = 5.0        # > 5x: A-rated quality
    INTEREST_COVERAGE_ADEQUATE = 2.5       # > 2.5x: BBB-rated (acceptable)
    INTEREST_COVERAGE_WEAK = 1.5           # > 1.5x: High-yield (risky)
    INTEREST_COVERAGE_DISTRESSED = 1.0     # < 1x: Bankruptcy risk
    
    ROE_MIN = -1.00             # -100% ROE (severe losses)
    ROE_MAX = 1.00              # +100% ROE (exceptional returns)
    
    CURRENT_RATIO_MIN = 0.50    # < 0.5x: liquidity stress
    CURRENT_RATIO_ACCEPTABLE = 1.00  # 1-2x is normal
    CURRENT_RATIO_EXCELLENT = 2.00   # > 2x: conservative
    
    def __init__(self, company_name: str = ""):
        """
        Args:
            company_name: Ticker or company name (for logging)
        """
        self.company_name = company_name
        self.errors = []
        self.warnings = []
    
    def validate_all(self, inputs: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Run comprehensive validation on financial inputs
        
        Args:
            inputs: Dictionary with financial metrics
        
        Returns:
            Tuple: (is_valid, errors_list, warnings_list)
        """
        self.errors = []
        self.warnings = []
        
        # Run all validation checks
        self._validate_scale_checks(inputs)
        self._validate_profitability(inputs)
        self._validate_leverage(inputs)
        self._validate_liquidity(inputs)
        self._validate_margins(inputs)
        self._validate_growth_consistency(inputs)
        self._validate_data_completeness(inputs)
        
        is_valid = len(self.errors) == 0
        
        # Log results
        logger.info(f"\nValidation Summary for {self.company_name}:")
        logger.info(f"  Status: {'✓ VALID' if is_valid else '✗ INVALID'}")
        logger.info(f"  Errors:   {len(self.errors)}")
        logger.info(f"  Warnings: {len(self.warnings)}")
        
        return is_valid, self.errors, self.warnings
    
    def _validate_scale_checks(self, inputs: Dict) -> None:
        """Check if financial metrics are in realistic ranges"""
        
        logger.info("\n[1/6] SCALE CHECKS")
        
        # Revenue validation
        revenue = inputs.get('revenue', 0)
        if revenue < self.REVENUE_MIN_M:
            self.errors.append(f"Revenue ${revenue:.0f}M below minimum threshold ($1M)")
        elif revenue > self.REVENUE_MAX_M:
            self.errors.append(f"Revenue ${revenue:.0f}M exceeds maximum threshold ($1T)")
        else:
            logger.info(f"  ✓ Revenue: ${revenue:,.0f}M (valid)")
        
        # Shares outstanding validation
        shares = inputs.get('shares', 0)
        shares_m = shares / 1e6
        if shares_m < self.SHARES_MIN_M:
            self.errors.append(f"Shares {shares_m:.2f}M below minimum ($0.1M)")
        elif shares_m > self.SHARES_MAX_M:
            self.errors.append(f"Shares {shares_m:.1f}M exceeds maximum (10B)")
        else:
            logger.info(f"  ✓ Shares: {shares_m:,.1f}M (valid)")
        
        # EBIT validation
        ebit = inputs.get('ebit', 0)
        if revenue > 0:
            ebit_margin = ebit / revenue
            if ebit_margin < self.EBIT_MARGIN_MIN:
                self.errors.append(f"EBIT margin {ebit_margin:.1%} below minimum (-50%)")
            elif ebit_margin > self.EBIT_MARGIN_MAX:
                self.errors.append(f"EBIT margin {ebit_margin:.1%} exceeds maximum (+70%)")
            else:
                logger.info(f"  ✓ EBIT Margin: {ebit_margin:.1%} (valid)")
    
    def _validate_profitability(self, inputs: Dict) -> None:
        """Check profitability metrics"""
        
        logger.info("\n[2/6] PROFITABILITY CHECKS")
        
        revenue = inputs.get('revenue', 1)
        ebit = inputs.get('ebit', 0)
        net_income = inputs.get('net_income', 0)
        
        # Unprofitable company check
        if ebit < 0:
            self.warnings.append("EBIT is negative (unprofitable operations)")
        else:
            logger.info(f"  ✓ EBIT Positive: ${ebit:,.0f}M")
        
        if net_income < 0:
            self.warnings.append("Net income negative (company loss-making)")
        else:
            logger.info(f"  ✓ Net Income Positive: ${net_income:,.0f}M")
        
        # EBIT to Net Income ratio
        if ebit > 0 and net_income > 0:
            ni_to_ebit = net_income / ebit
            if ni_to_ebit < 0.30 or ni_to_ebit > 1.0:
                self.warnings.append(f"Net Income/EBIT ratio {ni_to_ebit:.1%} unusual (check for taxes/interest)")
    
    def _validate_leverage(self, inputs: Dict) -> None:
        """Check debt and leverage ratios"""
        
        logger.info("\n[3/6] LEVERAGE CHECKS")
        
        ebit = inputs.get('ebit', 1)
        interest_exp = inputs.get('interest_exp', 0)
        debt = inputs.get('debt', 0)
        cash = inputs.get('cash', 0)
        
        # Interest coverage ratio
        if interest_exp > 0:
            ic = ebit / interest_exp
            
            if ic > self.INTEREST_COVERAGE_EXCELLENT:
                rating = "AAA/AA (Excellent)"
                logger.info(f"  ✓ Interest Coverage: {ic:.2f}x [{rating}]")
            elif ic > self.INTEREST_COVERAGE_HEALTHY:
                rating = "A (Strong)"
                logger.info(f"  ✓ Interest Coverage: {ic:.2f}x [{rating}]")
            elif ic > self.INTEREST_COVERAGE_ADEQUATE:
                rating = "BBB (Acceptable)"
                self.warnings.append(f"Interest coverage {ic:.2f}x [{rating}] - moderate debt risk")
            elif ic > self.INTEREST_COVERAGE_WEAK:
                rating = "BB (High-Yield)"
                self.warnings.append(f"Interest coverage {ic:.2f}x [{rating}] - elevated debt risk")
            else:
                rating = "B/Default (Distressed)"
                self.errors.append(f"Interest coverage {ic:.2f}x [{rating}] - acute default risk")
        else:
            if debt > 0:
                self.warnings.append("Debt reported but no interest expense (data inconsistency)")
        
        # Debt-to-Equity ratio
        if debt > 0:
            # Equity value = market cap
            equity_value = inputs.get('current_price', 0) * inputs.get('shares', 1) / 1e6
            if equity_value > 0:
                de_ratio = debt / equity_value
                
                if de_ratio < 0.5:
                    logger.info(f"  ✓ Debt-to-Equity: {de_ratio:.2f}x (conservative)")
                elif de_ratio < self.DEBT_TO_EQUITY_WARNING:
                    logger.info(f"  ✓ Debt-to-Equity: {de_ratio:.2f}x (normal)")
                elif de_ratio < self.DEBT_TO_EQUITY_ERROR:
                    self.warnings.append(f"Debt-to-Equity {de_ratio:.2f}x (elevated leverage)")
                else:
                    self.errors.append(f"Debt-to-Equity {de_ratio:.2f}x (excessive leverage)")
        
        # Net debt analysis
        net_debt = debt - cash
        if net_debt < 0:
            logger.info(f"  ✓ Net Cash Position: ${-net_debt:,.0f}M (positive)")
        else:
            logger.info(f"  ✓ Net Debt: ${net_debt:,.0f}M")
    
    def _validate_liquidity(self, inputs: Dict) -> None:
        """Check liquidity and working capital metrics"""
        
        logger.info("\n[4/6] LIQUIDITY CHECKS")
        
        cash = inputs.get('cash', 0)
        debt = inputs.get('debt', 0)
        
        # Cash position relative to revenue
        revenue = inputs.get('revenue', 1)
        cash_to_revenue = cash / revenue if revenue > 0 else 0
        
        if cash_to_revenue < 0.01:
            self.warnings.append(f"Cash/Revenue {cash_to_revenue:.1%} very low (liquidity squeeze)")
        elif cash_to_revenue > 0.50:
            logger.info(f"  ✓ Cash Position: {cash_to_revenue:.1%} of revenue (strong)")
        else:
            logger.info(f"  ✓ Cash Position: {cash_to_revenue:.1%} of revenue (normal)")
        
        # Cash relative to debt
        if debt > 0:
            cash_to_debt = cash / debt
            if cash_to_debt > 1.0:
                logger.info(f"  ✓ Cash covers all debt {cash_to_debt:.1f}x (strong position)")
            elif cash_to_debt > 0.5:
                logger.info(f"  ✓ Cash covers {cash_to_debt:.1%} of debt")
            elif cash_to_debt > 0.1:
                self.warnings.append(f"Cash only covers {cash_to_debt:.1%} of debt")
            else:
                self.warnings.append(f"Minimal cash vs debt (refinancing risk)")
    
    def _validate_margins(self, inputs: Dict) -> None:
        """Check operating margins and efficiency"""
        
        logger.info("\n[5/6] MARGIN CHECKS")
        
        revenue = inputs.get('revenue', 1)
        ebit = inputs.get('ebit', 0)
        net_income = inputs.get('net_income', 0)
        
        # EBIT margin
        if revenue > 0:
            ebit_margin = ebit / revenue
            if ebit_margin < 0:
                logger.info(f"  ⚠ EBIT Margin: {ebit_margin:.1%} (unprofitable)")
            elif ebit_margin < 0.05:
                self.warnings.append(f"EBIT margin {ebit_margin:.1%} low (thin operations)")
            elif ebit_margin > 0.40:
                logger.info(f"  ✓ EBIT Margin: {ebit_margin:.1%} (strong/premium)")
            else:
                logger.info(f"  ✓ EBIT Margin: {ebit_margin:.1%} (normal)")
            
            # Net margin
            net_margin = net_income / revenue
            if net_margin < 0:
                logger.info(f"  ⚠ Net Margin: {net_margin:.1%} (unprofitable)")
            elif net_margin < ebit_margin - 0.15:
                self.warnings.append(f"High interest/tax burden reducing net margin")
            else:
                logger.info(f"  ✓ Net Margin: {net_margin:.1%}")
    
    def _validate_growth_consistency(self, inputs: Dict) -> None:
        """Check for data consistency issues related to growth"""
        
        logger.info("\n[6/6] GROWTH CONSISTENCY CHECKS")
        
        revenue = inputs.get('revenue', 0)
        ebit = inputs.get('ebit', 0)
        net_income = inputs.get('net_income', 0)
        
        # Sanity: Is operating income less than revenue?
        if revenue > 0 and ebit > revenue:
            self.warnings.append("EBIT exceeds revenue (possible data error)")
        
        # Sanity: Is net income less than EBIT (should be with taxes)?
        if ebit > 0 and net_income > ebit:
            self.warnings.append("Net income exceeds EBIT (data inconsistency)")
        
        logger.info("  ✓ No critical growth inconsistencies detected")
    
    def _validate_data_completeness(self, inputs: Dict) -> None:
        """Check for missing critical data fields"""
        
        logger.info("\n[COMPLETENESS CHECK]")
        
        required_fields = [
            'revenue', 'ebit', 'net_income', 'shares', 
            'debt', 'cash', 'current_price'
        ]
        
        missing = [f for f in required_fields if f not in inputs or inputs[f] is None]
        
        if missing:
            self.warnings.append(f"Missing fields: {', '.join(missing)}")
        else:
            logger.info("  ✓ All critical fields present")
    
    def get_health_score(self, inputs: Dict) -> float:
        """
        Calculate overall financial health score (0-100)
        
        Weighted factors:
        - Profitability (25%)
        - Leverage (25%)
        - Liquidity (20%)
        - Margins (20%)
        - Growth consistency (10%)
        """
        
        score = 100
        
        # Profitability penalty
        revenue = inputs.get('revenue', 1)
        net_income = inputs.get('net_income', 0)
        if revenue > 0:
            net_margin = net_income / revenue
            if net_margin < 0.02:
                score -= 15  # Low profitability
            elif net_margin > 0.20:
                score -= 5   # Unusually high (might need validation)
        
        # Leverage penalty
        ebit = inputs.get('ebit', 1)
        interest_exp = inputs.get('interest_exp', 0)
        if interest_exp > 0:
            ic = ebit / interest_exp
            if ic < 1.5:
                score -= 20  # High default risk
            elif ic < 2.5:
                score -= 10  # Moderate risk
        
        # Liquidity check
        cash = inputs.get('cash', 0)
        debt = inputs.get('debt', 0)
        if debt > 0 and cash < debt * 0.10:
            score -= 10  # Limited liquidity
        
        return max(0, score)  # Floor at 0


def validate_sec_inputs(inputs: Dict, company_name: str = "") -> Tuple[bool, Dict]:
    """
    Convenience function to validate SEC-fetched inputs
    
    Returns:
        Tuple: (is_valid, validation_report)
    """
    
    validator = FinancialDataValidator(company_name)
    is_valid, errors, warnings = validator.validate_all(inputs)
    
    health_score = validator.get_health_score(inputs)
    
    report = {
        'is_valid': is_valid,
        'errors': errors,
        'warnings': warnings,
        'health_score': health_score,
        'summary': f"Financial Health: {health_score:.0f}/100"
    }
    
    return is_valid, report


# Example usage
if __name__ == "__main__":
    
    # Test with Google-like financials
    test_inputs_good = {
        'revenue': 280_000,
        'ebit': 80_000,
        'net_income': 59_000,
        'shares': 12_700e6,
        'debt': 13_000,
        'cash': 110_000,
        'current_price': 140,
        'interest_exp': 300
    }
    
    # Test with distressed company
    test_inputs_bad = {
        'revenue': 100,
        'ebit': -50,
        'net_income': -100,
        'shares': 1000e6,
        'debt': 500,
        'cash': 10,
        'current_price': 1,
        'interest_exp': 100
    }
    
    print("=" * 70)
    print("VALIDATING HEALTHY COMPANY")
    print("=" * 70)
    is_valid1, report1 = validate_sec_inputs(test_inputs_good, "GOOGL")
    print(f"\nValidation Result: {'✓ PASS' if is_valid1 else '✗ FAIL'}")
    print(f"Health Score: {report1['health_score']:.0f}/100")
    
    print("\n" + "=" * 70)
    print("VALIDATING DISTRESSED COMPANY")
    print("=" * 70)
    is_valid2, report2 = validate_sec_inputs(test_inputs_bad, "DISTRESSED")
    print(f"\nValidation Result: {'✓ PASS' if is_valid2 else '✗ FAIL'}")
    print(f"Health Score: {report2['health_score']:.0f}/100")
    if report2['errors']:
        print(f"\nErrors ({len(report2['errors'])}):")
        for error in report2['errors']:
            print(f"  ✗ {error}")
    if report2['warnings']:
        print(f"\nWarnings ({len(report2['warnings'])}):")
        for warning in report2['warnings']:
            print(f"  ⚠ {warning}")
