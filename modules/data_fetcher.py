
import yfinance as yf
import pandas as pd
import streamlit as st
import requests

class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker
        # We initialize the ticker object
        self.stock = yf.Ticker(ticker)

    @st.cache_data(ttl=3600)
    def get_valuation_inputs(_self):
        """Fetches audited data with professional headers to avoid rate limits"""
        try:
            # We use a session with a real browser User-Agent
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Re-initialize with session
            _self.stock = yf.Ticker(_self.ticker, session=session)
            
            # Fetching Statement Data
            income = _self.stock.financials
            bs = _self.stock.balance_sheet
            cf = _self.stock.cashflow
            info = _self.stock.info
            
            if income.empty or bs.empty:
                st.error("Financial statements are empty. Yahoo Finance may be blocking the request.")
                return None

            def get_val(df, labels):
                for label in labels:
                    if label in df.index:
                        return df.loc[label].iloc[0]
                return 0

            # Extraction Logic (Standardizing to Millions)
            revenue = get_val(income, ['Total Revenue', 'Operating Revenue']) / 1e6
            ebit = get_val(income, ['Ebit', 'Operating Income']) / 1e6
            tax_exp = get_val(income, ['Tax Provision', 'Income Tax Expense']) / 1e6
            total_debt = get_val(bs, ['Total Debt', 'Long Term Debt']) / 1e6
            cash = get_val(bs, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments']) / 1e6
            capex = abs(get_val(cf, ['Capital Expenditure', 'Net PPE Purchase And Sale'])) / 1e6
            depr = get_val(cf, ['Depreciation And Amortization', 'Depreciation']) / 1e6

            return {
                "name": info.get('longName', _self.ticker),
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
            st.error(f"SEC Data Error: {str(e)}")
            return None
