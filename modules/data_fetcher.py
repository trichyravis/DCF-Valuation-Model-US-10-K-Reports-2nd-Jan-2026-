
import yfinance as yf
import pandas as pd
import streamlit as st

class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)

    def get_valuation_inputs(self):
        """Fetches audited financial data and standardizes to Millions ($M)"""
        try:
            # Fetching Statement Data
            income = self.stock.financials
            bs = self.stock.balance_sheet
            cf = self.stock.cashflow
            info = self.stock.info
            
            # Helper to handle missing labels across different company filings
            def get_val(df, labels):
                for label in labels:
                    if label in df.index:
                        return df.loc[label].iloc[0]
                return 0

            # Extraction Logic (Standardizing to Millions)
            revenue = get_val(income, ['Total Revenue', 'Operating Revenue']) / 1e6
            ebit = get_val(income, ['Ebit', 'Operating Income']) / 1e6
            tax_exp = get_val(income, ['Tax Provision', 'Income Tax Expense']) / 1e6
            
            # Balance Sheet Items
            total_debt = get_val(bs, ['Total Debt', 'Long Term Debt']) / 1e6
            cash = get_val(bs, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments']) / 1e6
            
            # Cash Flow Items
            capex = abs(get_val(cf, ['Capital Expenditure', 'Net PPE Purchase And Sale'])) / 1e6
            depr = get_val(cf, ['Depreciation And Amortization', 'Depreciation']) / 1e6

            return {
                "name": info.get('longName', self.ticker),
                "revenue": revenue,
                "ebit": ebit,
                "tax_rate": abs(tax_exp / ebit) if ebit != 0 else 0.21,
                "capex": capex,
                "depr": depr,
                "debt": total_debt,
                "cash": cash,
                "shares": info.get('sharesOutstanding', 1)
            }
        except Exception as e:
            st.error(f"Error fetching SEC data for {self.ticker}: {str(e)}")
            return None
