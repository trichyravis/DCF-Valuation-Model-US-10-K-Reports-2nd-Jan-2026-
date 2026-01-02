
import pandas as pd
import streamlit as st
import requests
import time

class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker
        # SEC uses CIK (Central Index Key) for searches. 
        self.headers = {
            'User-Agent': 'Mountain Path Valuation terminal (your-email@example.com)',
            'Accept-Encoding': 'gzip, deflate'
        }

    @st.cache_data(ttl=3600)
    def get_valuation_inputs(_self):
        """Fetches audited data directly from SEC EDGAR API"""
        try:
            # 1. Get CIK from Ticker
            ticker_map = requests.get(
                "https://www.sec.gov/files/company_tickers.json", 
                headers=_self.headers
            ).json()
            
            cik = None
            for item in ticker_map.values():
                if item['ticker'] == _self.ticker.upper():
                    cik = str(item['cik_str']).zfill(10)
                    company_name = item['title']
                    break
            
            if not cik:
                st.error(f"Ticker {_self.ticker} not found in SEC database.")
                return None

            # 2. Fetch Company Facts (JSON)
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            facts = requests.get(facts_url, headers=_self.headers).json()
            
            # Helper to get latest year-end value from US-GAAP tags
            def get_sec_val(tag, taxonomy='us-gaap'):
                try:
                    data_points = facts['facts'][taxonomy][tag]['units']['USD']
                    # Filter for annual (10-K) filings or look for latest point
                    # We sort by 'end' date to get the most recent audited figure
                    latest = sorted(data_points, key=lambda x: x['end'])[-1]
                    return latest['val']
                except KeyError:
                    return 0

            # Extraction (SEC tags are very specific)
            revenue = get_sec_val('Revenues') or get_sec_val('RevenueFromContractWithCustomerExcludingCostReportedAmount')
            ebit = get_sec_val('OperatingIncomeLoss')
            tax_exp = get_sec_val('IncomeTaxExpenseBenefit')
            total_debt = get_sec_val('DebtCurrent') + get_sec_val('LongTermDebtNoncurrent')
            cash = get_sec_val('CashAndCashEquivalentsAtCarryingValue')
            # Shares are usually under 'dei' taxonomy
            shares = get_sec_val('EntityCommonStockSharesOutstanding', taxonomy='dei') or 1

            # Standardizing to Millions for your engine
            return {
                "name": company_name,
                "revenue": revenue / 1e6,
                "ebit": ebit / 1e6,
                "tax_rate": abs(tax_exp / ebit) if ebit != 0 else 0.21,
                "capex": get_sec_val('PaymentsToAcquirePropertyPlantAndEquipment') / 1e6,
                "depr": get_sec_val('DepreciationDepletionAndAmortization') / 1e6,
                "debt": total_debt / 1e6,
                "cash": cash / 1e6,
                "shares": shares
            }

        except Exception as e:
            st.error(f"SEC EDGAR API Error: {str(e)}")
            return None
