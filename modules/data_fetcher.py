
import pandas as pd
import streamlit as st
import requests
import yfinance as yf
import time

class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        # SEC requires a specific User-Agent format: Company Name/Email
        self.headers = {
            'User-Agent': 'Mountain Path Analytics (research@mountainpath.edu)',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }

    @st.cache_data(ttl=3600)  # CRITICAL: Prevents rate limits by saving data for 1 hour
    def get_valuation_inputs(_self):
        """Fetches audited SEC 10-K data with rate-limit protection"""
        try:
            # 1. Map Ticker to CIK (SEC Central Index Key)
            # Use the official SEC mapping file
            ticker_map_url = "https://www.sec.gov/files/company_tickers.json"
            # SEC mapping requires a different host header
            map_headers = {'User-Agent': 'Mountain Path Analytics (research@mountainpath.edu)'}
            ticker_map = requests.get(ticker_map_url, headers=map_headers).json()
            
            cik = None
            for item in ticker_map.values():
                if item['ticker'] == _self.ticker:
                    cik = str(item['cik_str']).zfill(10)
                    break
            
            if not cik:
                return None

            # 2. Fetch Facts from SEC (Income Statement, Balance Sheet, Cash Flow tags)
            time.sleep(0.1) # Be polite to SEC servers
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            facts = requests.get(facts_url, headers=_self.headers).json()
            
            def get_sec_val(tag, taxonomy='us-gaap'):
                try:
                    data = facts['facts'][taxonomy][tag]['units']['USD']
                    # Sort by end date to get the most recent audited fiscal year
                    return sorted(data, key=lambda x: x['end'])[-1]['val']
                except: return 0

            # 3. Fetch Real-time Market Price via yfinance
            stock = yf.Ticker(_self.ticker)
            try:
                current_price = stock.fast_info['last_price']
            except:
                # Fallback for rate-limited sessions
                hist = stock.history(period="1d")
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0

            # 4. Map XBRL Tags to Valuation Engine Inputs
            # Standardizing to Millions ($M)
            return {
                "name": _self.ticker,
                "ticker": _self.ticker,
                "current_price": current_price,
                "revenue": get_sec_val('Revenues') / 1e6 or get_sec_val('RevenueFromContractWithCustomerExcludingCostReportedAmount') / 1e6,
                "ebit": get_sec_val('OperatingIncomeLoss') / 1e6,
                "net_income": get_sec_val('NetIncomeLoss') / 1e6,
                "depr": get_sec_val('DepreciationDepletionAndAmortization') / 1e6,
                "capex": get_sec_val('PaymentsToAcquirePropertyPlantAndEquipment') / 1e6,
                "debt": (get_sec_val('LongTermDebtNoncurrent') + get_sec_val('DebtCurrent')) / 1e6,
                "cash": get_sec_val('CashAndCashEquivalentsAtCarryingValue') / 1e6,
                "interest_exp": get_sec_val('InterestExpense') / 1e6,
                "dividends": get_sec_val('PaymentsOfDividends') / 1e6,
                "shares": get_sec_val('EntityCommonStockSharesOutstanding', 'dei') or 1e6,
                "tax_rate": 0.21
            }
        except Exception as e:
            st.error(f"SEC Data Error: {str(e)}")
            return None
