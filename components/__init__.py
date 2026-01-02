
# __init__.py (Root)
"""
Mountain Path Valuation Terminal
Institutional Equity Valuation with Automated SEC Data Integration

Author: Prof. V. Ravichandran
Experience: 28+ Years Corporate Finance & Banking, 10+ Years Academic Excellence

This package provides a professional-grade DCF (Discounted Cash Flow) valuation
terminal that automatically integrates audited financial data from SEC 10-K filings.
"""

__version__ = '1.0.0'
__author__ = 'Prof. V. Ravichandran'
__project__ = 'The Mountain Path - World of Finance'
__description__ = 'Institutional Equity Valuation Terminal with SEC Data Integration'

# Import main modules for easy access
from components import header_component, sidebar_component, footer_component
from modules import SECDataFetcher, run_multi_valuation
from content import ABOUT_CONTENT, VALUATION_QA

__all__ = [
    'header_component',
    'sidebar_component',
    'footer_component',
    'SECDataFetcher',
    'run_multi_valuation',
    'ABOUT_CONTENT',
    'VALUATION_QA'
]
