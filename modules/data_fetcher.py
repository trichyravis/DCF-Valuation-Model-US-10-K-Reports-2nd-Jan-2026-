
import streamlit as st
import requests
import yfinance as yf
import json
import time


class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
    
    def get_valuation_inputs(self):
        try:
            # Step 1: Get ticker to CIK mapping
            ticker_map_url = "https://www.sec.gov/files/company_tickers.json"
            headers = {'User-Agent': 'Mountain Path Valuation (research@mountainpath.edu)'}
            
            try:
                response = requests.get(ticker_map_url, headers=headers, timeout=10)
                response.raise_for_status()
                ticker_map = response.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to fetch ticker mapping: {e}")
                return None
            
            # Step 2: Find CIK for this ticker
            cik = None
            for item in ticker_map.values():
                if item.get('ticker') == self.ticker:
                    cik = str(item.get('cik_str', '')).zfill(10)
                    break
            
            if not cik or cik == '0000000000':
                st.error(f"Ticker {self.ticker} not found")
                return None
            
            # Step 3: Fetch company facts from SEC
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            
            try:
                facts_response = requests.get(facts_url, headers=headers, timeout=10)
                facts_response.raise_for_status()
                facts = facts_response.json()
            except Exception as e:
                st.error(f"Failed to fetch SEC data: {e}")
                return None
            
            # Step 4: Extract financial values
            def get_val(tag, taxonomy='us-gaap'):
                try:
                    data = facts.get('facts', {}).get(taxonomy, {}).get(tag, {}).get('units', {}).get('USD', [])
                    if data:
                        return sorted(data, key=lambda x: x.get('end', ''))[-1].get('val', 0)
                    return 0
                except:
                    return 0
            
            def get_shares_from_sec():
                """Multiple strategies to fetch shares from SEC"""
                try:
                    # Strategy 1: Try DEI EntityCommonStockSharesOutstanding
                    dei_facts = facts.get('facts', {}).get('dei', {})
                    
                    if 'EntityCommonStockSharesOutstanding' in dei_facts:
                        ecsso = dei_facts['EntityCommonStockSharesOutstanding'].get('units', {})
                        
                        # Try 'pure' unit
                        if 'pure' in ecsso and ecsso['pure']:
                            val = sorted(ecsso['pure'], key=lambda x: x.get('end', ''))[-1].get('val', 0)
                            if val > 0:
                                return val
                        
                        # Try any unit
                        for unit_type, unit_data in ecsso.items():
                            if unit_data:
                                val = sorted(unit_data, key=lambda x: x.get('end', ''))[-1].get('val', 0)
                                if val > 0:
                                    return val
                    
                    # Strategy 2: Try us-gaap CommonStockSharesOutstanding
                    us_gaap = facts.get('facts', {}).get('us-gaap', {})
                    if 'CommonStockSharesOutstanding' in us_gaap:
                        csso = us_gaap['CommonStockSharesOutstanding'].get('units', {})
                        for unit_type, unit_data in csso.items():
                            if unit_data:
                                val = sorted(unit_data, key=lambda x: x.get('end', ''))[-1].get('val', 0)
                                if val > 0:
                                    return val
                    
                    return 0
                except:
                    return 0
            
            def get_current_price_robust():
                """
                Multiple strategies to fetch current price:
                1. yfinance info['currentPrice']
                2. yfinance info['regularMarketPrice']
                3. yfinance history last close
                4. yfinance fast_info
                5. Return 0 if all fail (don't error out)
                """
                try:
                    stock = yf.Ticker(self.ticker)
                    
                    # Strategy 1: Try info fields
                    info = stock.info
                    if info:
                        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                        if price and price > 0:
                            return float(price)
                    
                    # Strategy 2: Try fast_info
                    try:
                        fast_info = stock.fast_info
                        if fast_info:
                            price = fast_info.get('lastPrice')
                            if price and price > 0:
                                return float(price)
                    except:
                        pass
                    
                    # Strategy 3: Try history - 5 days
                    try:
                        hist = stock.history(period="5d")
                        if not hist.empty:
                            close_price = hist['Close'].iloc[-1]
                            if close_price > 0:
                                return float(close_price)
                    except:
                        pass
                    
                    # Strategy 4: Try history - 1 month
                    try:
                        hist = stock.history(period="1mo")
                        if not hist.empty:
                            close_price = hist['Close'].iloc[-1]
                            if close_price > 0:
                                return float(close_price)
                    except:
                        pass
                    
                    # All strategies failed, return 0
                    return 0
                
                except Exception as e:
                    return 0
            
            # Get shares
            shares_absolute = get_shares_from_sec()
            
            # Fallback to yfinance if SEC fails
            if shares_absolute == 0:
                try:
                    stock = yf.Ticker(self.ticker)
                    info = stock.info
                    shares_absolute = info.get('sharesOutstanding') or \
                                    info.get('floatShares') or \
                                    info.get('sharesFloat') or 0
                except:
                    pass
            
            # Convert shares to millions
            if shares_absolute > 1000000:
                shares_millions = shares_absolute / 1e6
            else:
                shares_millions = shares_absolute if shares_absolute > 0 else 1
            
            # Get current price with robust fallback
            current_price = get_current_price_robust()
            
            # Return all financial metrics
            return {
                "name": self.ticker,
                "current_price": current_price,
                # All in MILLIONS
                "revenue": get_val('Revenues') / 1e6 or get_val('RevenueFromContractWithCustomerExcludingCostReportedAmount') / 1e6,
                "ebit": get_val('OperatingIncomeLoss') / 1e6,
                "net_income": get_val('NetIncomeLoss') / 1e6,
                "depr": get_val('DepreciationDepletionAndAmortization') / 1e6,
                "capex": get_val('PaymentsToAcquirePropertyPlantAndEquipment') / 1e6,
                "debt": (get_val('LongTermDebtNoncurrent') + get_val('DebtCurrent')) / 1e6,
                "cash": get_val('CashAndCashEquivalentsAtCarryingValue') / 1e6,
                "interest_exp": get_val('InterestExpense') / 1e6,
                "dividends": get_val('PaymentsOfDividends') / 1e6,
                # SHARES IN MILLIONS
                "shares": shares_millions,
                "tax_rate": 0.21,
                "beta": 1.1
            }
        
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
