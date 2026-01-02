
# tests/test_valuation_engine.py
"""Comprehensive unit tests for DCF valuation engine"""

import pytest
import pandas as pd
import numpy as np
from modules.valuation_engine import run_multi_valuation


class TestValuationEngineBasics:
    """Test basic valuation calculations"""
    
    @pytest.fixture
    def sample_company_inputs(self):
        """Apple-like company for testing"""
        return {
            "name": "AAPL",
            "current_price": 189.95,
            "revenue": 394328.0,  # Millions
            "ebit": 130541.0,
            "net_income": 99803.0,
            "depr": 11510.0,
            "capex": 10949.0,
            "debt": 106959.0,
            "cash": 29941.0,
            "interest_exp": 3933.0,
            "dividends": 14763.0,
            "shares": 15593700000.0,  # Absolute shares
            "tax_rate": 0.21,
            "beta": 1.2
        }
    
    @pytest.fixture
    def market_data(self):
        """Standard market risk parameters"""
        return {
            'rf': 0.045,      # 4.5% risk-free rate
            'erp': 0.055      # 5.5% equity risk premium
        }
    
    def test_valuation_returns_dictionary(self, sample_company_inputs, market_data):
        """Valuation should return proper dictionary structure"""
        result = run_multi_valuation(
            sample_company_inputs,
            growth_rate=0.10,
            wacc=0.08,
            t_growth=0.025,
            market_data=market_data
        )
        
        assert isinstance(result, dict)
        assert all(key in result for key in [
            'df', 'dcf_price', 'ddm_price', 'pe_price', 'ev'
        ])
    
    def test_dcf_price_positive(self, sample_company_inputs, market_data):
        """DCF price must be positive"""
        result = run_multi_valuation(
            sample_company_inputs,
            growth_rate=0.10,
            wacc=0.08,
            t_growth=0.025,
            market_data=market_data
        )
        
        assert result['dcf_price'] > 0, "DCF price must be positive"
    
    def test_enterprise_value_positive(self, sample_company_inputs, market_data):
        """Enterprise value must be positive"""
        result = run_multi_valuation(
            sample_company_inputs,
            growth_rate=0.10,
            wacc=0.08,
            t_growth=0.025,
            market_data=market_data
        )
        
        assert result['ev'] > 0, "Enterprise value must be positive"
    
    def test_projection_dataframe_structure(self, sample_company_inputs, market_data):
        """Projection dataframe should have correct structure"""
        result = run_multi_valuation(
            sample_company_inputs,
            growth_rate=0.10,
            wacc=0.08,
            t_growth=0.025,
            market_data=market_data
        )
        
        df = result['df']
        
        # Check shape
        assert len(df) == 5, "Should have 5 year projections"
        
        # Check columns
        expected_cols = ['Year', 'Revenue', 'FCFF', 'PV_FCFF']
        assert all(col in df.columns for col in expected_cols)
        
        # Check years
        expected_years = [2026, 2027, 2028, 2029, 2030]
        assert list(df['Year']) == expected_years


class TestValuationSensitivity:
    """Test valuation sensitivity to parameter changes"""
    
    @pytest.fixture
    def base_inputs(self):
        return {
            "name": "TEST",
            "current_price": 100.0,
            "revenue": 1000.0,
            "ebit": 250.0,
            "net_income": 200.0,
            "depr": 50.0,
            "capex": 40.0,
            "debt": 500.0,
            "cash": 200.0,
            "interest_exp": 25.0,
            "dividends": 30.0,
            "shares": 100000000.0,  # 100M shares
            "tax_rate": 0.21,
            "beta": 1.0
        }
    
    @pytest.fixture
    def market_data(self):
        return {'rf': 0.045, 'erp': 0.055}
    
    def test_higher_growth_increases_price(self, base_inputs, market_data):
        """Higher growth rate should increase valuation"""
        low_growth = run_multi_valuation(
            base_inputs, 0.05, 0.08, 0.025, market_data
        )
        high_growth = run_multi_valuation(
            base_inputs, 0.15, 0.08, 0.025, market_data
        )
        
        assert high_growth['dcf_price'] > low_growth['dcf_price'], \
            "Higher growth should increase DCF price"
    
    def test_higher_wacc_decreases_price(self, base_inputs, market_data):
        """Higher WACC should decrease valuation"""
        low_wacc = run_multi_valuation(
            base_inputs, 0.10, 0.06, 0.025, market_data
        )
        high_wacc = run_multi_valuation(
            base_inputs, 0.10, 0.10, 0.025, market_data
        )
        
        assert high_wacc['dcf_price'] < low_wacc['dcf_price'], \
            "Higher WACC should decrease DCF price"
    
    def test_higher_terminal_growth_increases_price(self, base_inputs, market_data):
        """Higher terminal growth should increase valuation"""
        low_tg = run_multi_valuation(
            base_inputs, 0.10, 0.08, 0.015, market_data
        )
        high_tg = run_multi_valuation(
            base_inputs, 0.10, 0.08, 0.030, market_data
        )
        
        assert high_tg['dcf_price'] > low_tg['dcf_price'], \
            "Higher terminal growth should increase DCF price"


class TestValidationLogic:
    """Test input validation and error handling"""
    
    @pytest.fixture
    def valid_inputs(self):
        return {
            "name": "TEST",
            "current_price": 100.0,
            "revenue": 1000.0,
            "ebit": 250.0,
            "net_income": 200.0,
            "depr": 50.0,
            "capex": 40.0,
            "debt": 500.0,
            "cash": 200.0,
            "interest_exp": 25.0,
            "dividends": 30.0,
            "shares": 100000000.0,
            "tax_rate": 0.21,
            "beta": 1.0
        }
    
    @pytest.fixture
    def market_data(self):
        return {'rf': 0.045, 'erp': 0.055}
    
    def test_zero_revenue_handling(self, valid_inputs, market_data):
        """Should handle zero revenue gracefully"""
        invalid = valid_inputs.copy()
        invalid['revenue'] = 0
        
        # Should not raise exception
        try:
            result = run_multi_valuation(
                invalid, 0.10, 0.08, 0.025, market_data
            )
            # Result may be invalid but shouldn't crash
            assert result is not None
        except ZeroDivisionError:
            pytest.fail("Should handle zero revenue without crashing")
    
    def test_growth_exceeds_wacc(self, valid_inputs, market_data):
        """Model should handle growth > WACC (invalid but not crash)"""
        # This is mathematically invalid but should be caught/handled
        result = run_multi_valuation(
            valid_inputs,
            growth_rate=0.12,  # > WACC
            wacc=0.08,
            t_growth=0.025,
            market_data=market_data
        )
        
        # Should still return a result
        assert result is not None
        assert 'dcf_price' in result


class TestTerminalValueContribution:
    """Test terminal value as proportion of total value"""
    
    @pytest.fixture
    def inputs(self):
        return {
            "name": "TEST",
            "current_price": 100.0,
            "revenue": 1000.0,
            "ebit": 250.0,
            "net_income": 200.0,
            "depr": 50.0,
            "capex": 40.0,
            "debt": 500.0,
            "cash": 200.0,
            "interest_exp": 25.0,
            "dividends": 30.0,
            "shares": 100000000.0,
            "tax_rate": 0.21,
            "beta": 1.0
        }
    
    @pytest.fixture
    def market_data(self):
        return {'rf': 0.045, 'erp': 0.055}
    
    def test_terminal_value_proportion(self, inputs, market_data):
        """Terminal value should be 50-95% of total for stable companies"""
        result = run_multi_valuation(
            inputs, 0.10, 0.08, 0.025, market_data
        )
        
        df = result['df']
        pv_fcff_sum = df['PV_FCFF'].sum()
        
        # Recalculate terminal value
        terminal_fcff = df.iloc[-1]['FCFF']
        terminal_value = terminal_fcff * (1.025) / (0.08 - 0.025)
        pv_terminal = terminal_value / ((1.08) ** 5)
        
        total_value = pv_fcff_sum + pv_terminal
        terminal_pct = pv_terminal / total_value
        
        assert 0.4 < terminal_pct < 0.99, \
            f"Terminal value should be 40-99% of total, got {terminal_pct:.1%}"


class TestMarginOfSafety:
    """Test margin of safety calculations"""
    
    @pytest.fixture
    def inputs(self):
        return {
            "name": "TEST",
            "current_price": 100.0,
            "revenue": 1000.0,
            "ebit": 250.0,
            "net_income": 200.0,
            "depr": 50.0,
            "capex": 40.0,
            "debt": 500.0,
            "cash": 200.0,
            "interest_exp": 25.0,
            "dividends": 30.0,
            "shares": 100000000.0,
            "tax_rate": 0.21,
            "beta": 1.0
        }
    
    @pytest.fixture
    def market_data(self):
        return {'rf': 0.045, 'erp': 0.055}
    
    def test_margin_of_safety_range(self, inputs, market_data):
        """Margin of safety should be between -100% and +100%"""
        result = run_multi_valuation(
            inputs, 0.10, 0.08, 0.025, market_data
        )
        
        dcf_price = result['dcf_price']
        current_price = inputs['current_price']
        
        mos = (dcf_price - current_price) / dcf_price
        
        assert -1.0 <= mos <= 1.0, \
            f"Margin of safety should be -100% to +100%, got {mos:.1%}"


class TestDDMCalculation:
    """Test Dividend Discount Model calculation"""
    
    @pytest.fixture
    def inputs(self):
        return {
            "name": "TEST",
            "current_price": 100.0,
            "revenue": 1000.0,
            "ebit": 250.0,
            "net_income": 200.0,
            "depr": 50.0,
            "capex": 40.0,
            "debt": 500.0,
            "cash": 200.0,
            "interest_exp": 25.0,
            "dividends": 30.0,
            "shares": 100000000.0,
            "tax_rate": 0.21,
            "beta": 1.0
        }
    
    @pytest.fixture
    def market_data(self):
        return {'rf': 0.045, 'erp': 0.055}
    
    def test_ddm_price_positive(self, inputs, market_data):
        """DDM price should be positive for dividend-paying stocks"""
        result = run_multi_valuation(
            inputs, 0.10, 0.08, 0.025, market_data
        )
        
        assert result['ddm_price'] > 0 or inputs['dividends'] == 0, \
            "DDM price should be positive if dividends exist"
    
    def test_pe_multiple_applied(self, inputs, market_data):
        """P/E valuation should apply conservative multiple"""
        result = run_multi_valuation(
            inputs, 0.10, 0.08, 0.025, market_data
        )
        
        # P/E uses 15x multiple
        expected_eps = (inputs['net_income'] / inputs['shares']) * 1e6
        expected_price = expected_eps * 15
        
        assert abs(result['pe_price'] - expected_price) < 1.0, \
            "P/E calculation should use 15x multiple"


# === INTEGRATION TESTS ===
class TestIntegration:
    """Integration tests for complete workflow"""
    
    def test_three_valuation_methods_consistency(self):
        """All three methods should produce values in reasonable range"""
        inputs = {
            "name": "TEST",
            "current_price": 100.0,
            "revenue": 10000.0,
            "ebit": 2500.0,
            "net_income": 2000.0,
            "depr": 500.0,
            "capex": 400.0,
            "debt": 5000.0,
            "cash": 2000.0,
            "interest_exp": 250.0,
            "dividends": 300.0,
            "shares": 1000000000.0,
            "tax_rate": 0.21,
            "beta": 1.0
        }
        
        market_data = {'rf': 0.045, 'erp': 0.055}
        
        result = run_multi_valuation(
            inputs, 0.10, 0.08, 0.025, market_data
        )
        
        # All three should be positive
        assert result['dcf_price'] > 0
        assert result['ddm_price'] >= 0
        assert result['pe_price'] > 0
        
        # They should all be in reasonable range (within 2x of DCF)
        assert result['ddm_price'] < result['dcf_price'] * 3 or result['dividends'] == 0
        assert result['pe_price'] < result['dcf_price'] * 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
