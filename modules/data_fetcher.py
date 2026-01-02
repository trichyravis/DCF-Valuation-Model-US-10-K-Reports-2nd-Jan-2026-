
import requests
import streamlit as st

class SECDataFetcher:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        # SEC requires an identifying User-Agent with an email
        self.headers = {
            'User-Agent': 'Mountain Path Valuation research@mountainpath.edu',
            'Accept-Encoding': 'gzip, deflate'
        }

    @st.cache_data(ttl=3600)  # Prevents repeated API calls during the same session
    def get_valuation_inputs(_self):
        try:
            # Step 1: Get CIK
            ticker_url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(ticker_url, headers=_self.headers)
            
            # CHECK: If response is empty, return None instead of crashing
            if not response.text.strip():
                st.error("SEC API returned an empty response. You may be rate-limited.")
                return None
                
            ticker_map = response.json()
            # ... (rest of your CIK mapping logic)
            
            # Step 2: Fetch Company Facts
            facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            facts_response = requests.get(facts_url, headers=_self.headers)
            
            # SAFETY: Ensure the body is not empty before parsing JSON
            if facts_response.status_code == 200 and facts_response.text.strip():
                return facts_response.json()
            else:
                st.warning(f"No data found for {_self.ticker} in SEC archives.")
                return None

        except requests.exceptions.JSONDecodeError:
            st.error("Failed to parse SEC data. The API may be unavailable.")
            return None
