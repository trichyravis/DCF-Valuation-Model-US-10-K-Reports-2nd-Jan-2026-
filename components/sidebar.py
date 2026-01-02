
import streamlit as st

def sidebar_component():
    """Valuation inputs and configuration"""
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #002147 !important; }
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label { 
            color: white !important; font-weight: bold; 
        }
        div.stButton > button:first-child {
            background-color: #FFD700 !important; color: #002147 !important;
            font-weight: bold !important; width: 100%; border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("🏢 Target Selection")
        ticker = st.text_input("US Ticker (Audited 10-K Search)", value="GOOGL").upper()
        
        st.header("📈 Growth Assumptions")
        # Growth for Stage 1 (5 years)
        growth_rate = st.slider("Step 1: Revenue Growth (%)", 0.0, 30.0, 15.0) / 100
        
        st.header("🛡️ Discount & Terminal")
        wacc = st.slider("WACC (%)", 5.0, 15.0, 7.5) / 100
        t_growth = st.slider("Terminal Growth (%)", 1.0, 5.0, 2.5) / 100
        
        st.markdown("---")
        run_val = st.button("📊 EXECUTE AUDITED DCF")
        
    return ticker, growth_rate, wacc, t_growth, run_val


# ============================================================================
# USAGE EXAMPLE
# ============================================================================
if __name__ == "__main__":
    # Call the sidebar component
    ticker, growth_rate, wacc, t_growth, run_val = sidebar_component()
    
    # Display the retrieved values
    st.title("DCF Valuation Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ticker", ticker)
    with col2:
        st.metric("Growth Rate", f"{growth_rate*100:.1f}%")
    with col3:
        st.metric("WACC", f"{wacc*100:.1f}%")
    with col4:
        st.metric("Terminal Growth", f"{t_growth*100:.1f}%")
    
    if run_val:
        st.success("✅ Valuation Model Executed Successfully!")
        st.write(f"Running DCF analysis for {ticker}...")
