
import pandas as pd
import streamlit as st
import requests
import yfinance as yf
import time

class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.headers = {
            'User-Agent': 'Mountain Path Valuation research@mountainpath.edu',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }

    def get_valuation_inputs(self):
        # We pass self.ticker as the primary 'hash key'
        # We underscore _self and _headers so Streamlit ignores them for hashing
        return self._fetch_ticker_data(self.ticker, self, self.headers)

    @st.cache_data(ttl=3600)
    def _fetch_ticker_data(ticker_str, _self, _headers):
        """
        Streamlit hashes 'ticker_str' to decide if it should rerun.
        The underscore in '_self' and '_headers' tells Streamlit:
        'Don't try to hash these; just pass them through.'
        """
        try:
            # 1. Map Ticker to CIK
            ticker_map_url = "https://www.sec.gov/files/company_tickers.json"
            map_headers = {'User-Agent': 'MPV/1.0 research@mountainpath.edu'}
            response = requests.get(ticker_map_url, headers=map_headers)
            
            if not response.text.strip(): return None
            ticker_map = response.json()
            
            cik = None 
            for item in ticker_map.values():
                if item['ticker'] == ticker_str:
                    cik = str(item['cik_str']).zfill(10)
                    break
            
            if not cik: return None

            # 2. Fetch Audited Facts
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            # Use the ignored _headers parameter
            facts_res = requests.get(facts_url, headers=_headers)
            facts = facts_res.json()
            
            def get_val(tag, taxonomy='us-gaap'):
                try:
                    data = facts['facts'][taxonomy][tag]['units']['USD']
                    return sorted(data, key=lambda x: x['end'])[-1]['val']
                except: return 0

            # 3. Market Price
            stock = yf.Ticker(ticker_str)
            hist = stock.history(period="1d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0

            return {
                "name": ticker_str,
                "current_price": current_price,
                "revenue": get_val('Revenues') / 1e6 or get_val('RevenueFromContractWithCustomerExcludingCostReportedAmount') / 1e6,
                "ebit": get_val('OperatingIncomeLoss') / 1e6,
                "net_income": get_val('NetIncomeLoss') / 1e6,
                "depr": get_val('DepreciationDepletionAndAmortization') / 1e6,
                "capex": get_val('PaymentsToAcquirePropertyPlantAndEquipment') / 1e6,
                "debt": (get_val('LongTermDebtNoncurrent') + get_val('DebtCurrent')) / 1e6,
                "cash": get_val('CashAndCashEquivalentsAtCarryingValue') / 1e6,
                "interest_exp": get_val('InterestExpense') / 1e6,
                "dividends": get_val('PaymentsOfDividends') / 1e6,
                "shares": get_val('EntityCommonStockSharesOutstanding', 'dei') or 1e6,
                "tax_rate": 0.21,
                "beta": 1.1
            }
        except Exception as e:
            st.error(f"Fetch Error: {e}")
            return None
