# main.py - COMPLETE STREAMLIT APPLICATION ENTRY POINT
# The Mountain Path: Institutional Equity Valuation Terminal
# Prof. V. Ravichandran | Advanced Financial Education

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import logging

# === IMPORTS FROM PROJECT MODULES ===
from components.header import header_component
from components.sidebar import sidebar_component
from components.footer import footer_component
from modules.data_fetcher import SECDataFetcher
from modules.valuation_engine import run_multi_valuation
from content.valuation_qa import VALUATION_QA
from content.about_text import ABOUT_CONTENT

# === LOGGING SETUP ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === PAGE CONFIGURATION ===
st.set_page_config(
    page_title="🏔️ Mountain Path Valuation Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS ===
st.markdown("""
    <style>
    .metric-box {
        background: linear-gradient(135deg, #002147 0%, #004b8d 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #FFD700;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #ffffff;
        margin-top: 5px;
    }
    .success-box {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        color: #155724;
        margin-bottom: 15px;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 15px;
        color: #856404;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)


def render_valuation_analysis(ticker: str, growth_rate: float, 
                              wacc: float, t_growth: float) -> None:
    """Main DCF valuation analysis section"""
    
    st.subheader(f"📊 DCF Valuation Analysis: {ticker}")
    
    # === FETCH SEC DATA ===
    with st.spinner(f"📥 Fetching audited financial data for {ticker}..."):
        fetcher = SECDataFetcher(ticker)
        inputs = fetcher.get_valuation_inputs()
    
    if inputs is None:
        st.error(f"❌ Unable to fetch data for {ticker}. Please verify ticker and try again.")
        return
    
    # === DISPLAY FETCHED DATA ===
    with st.expander("📋 Audited Financial Data (from SEC 10-K)", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Revenue ($M)", f"${inputs['revenue']:,.0f}")
            st.metric("EBIT ($M)", f"${inputs['ebit']:,.0f}")
            st.metric("EBIT Margin", f"{(inputs['ebit']/inputs['revenue']*100):.1f}%")
        
        with col2:
            st.metric("Net Income ($M)", f"${inputs['net_income']:,.0f}")
            st.metric("Debt ($M)", f"${inputs['debt']:,.0f}")
            st.metric("Cash ($M)", f"${inputs['cash']:,.0f}")
        
        with col3:
            st.metric("Shares (M)", f"{inputs['shares']/1e6:,.0f}")
            st.metric("Current Price", f"${inputs['current_price']:.2f}")
            st.metric("Market Cap ($M)", f"${(inputs['current_price'] * inputs['shares'] / 1e6):,.0f}")
    
    # === RUN VALUATION ===
    market_data = {
        'rf': 0.045,  # 4.5% risk-free rate
        'erp': 0.055  # 5.5% equity risk premium
    }
    
    with st.spinner("🔄 Computing DCF valuation..."):
        result = run_multi_valuation(inputs, growth_rate, wacc, t_growth, market_data)
    
    # === VALUATION RESULTS ===
    st.markdown("---")
    st.subheader("💰 Valuation Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Enterprise Value</div>
            <div class="metric-value">${result['ev']/1000:.1f}B</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Fair Value Per Share</div>
            <div class="metric-value">${result['dcf_price']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        upside_pct = ((result['dcf_price'] - inputs['current_price']) / inputs['current_price'] * 100) if inputs['current_price'] > 0 else 0
        color = "#28a745" if upside_pct > 0 else "#dc3545"
        st.markdown(f"""
        <div class="metric-box" style="background: linear-gradient(135deg, {color} 0%, {color}88 100%);">
            <div class="metric-label">Upside/Downside</div>
            <div class="metric-value">{upside_pct:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        margin_of_safety = ((result['dcf_price'] - inputs['current_price']) / result['dcf_price'] * 100) if result['dcf_price'] > 0 else 0
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Margin of Safety</div>
            <div class="metric-value">{margin_of_safety:+.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # === VALUATION BREAKDOWN ===
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 5-Year Projection Detail")
        st.dataframe(
            result['df'][['Year', 'Revenue', 'FCFF', 'PV_FCFF']].style.format({
                'Revenue': '${:,.0f}',
                'FCFF': '${:,.0f}',
                'PV_FCFF': '${:,.0f}'
            }),
            use_container_width=True
        )
    
    with col2:
        st.subheader("🎯 Value Composition")
        
        # Value breakdown pie chart
        pv_fcff_sum = result['df']['PV_FCFF'].sum()
        pv_terminal = result['df']['PV_FCFF'].iloc[-1] * (1 + t_growth) / (wacc - t_growth) / ((1 + wacc) ** 5)
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=['5-Yr FCFF', 'Terminal Value'],
            values=[pv_fcff_sum, pv_terminal],
            marker=dict(colors=['#002147', '#FFD700']),
            hovertemplate='<b>%{label}</b><br>Value: $%{value:,.0f}M<br>Share: %{percent}<extra></extra>'
        )])
        
        fig_pie.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # === COMPARISON WITH DDM & P/E ===
    st.markdown("---")
    st.subheader("🔀 Multiple Valuation Approaches")
    
    comparison_data = {
        'Method': ['DCF (FCFF)', 'DDM (Dividend)', 'P/E Multiple'],
        'Fair Value': [
            f"${result['dcf_price']:.2f}",
            f"${result['ddm_price']:.2f}",
            f"${result['pe_price']:.2f}"
        ],
        'Methodology': [
            'Free Cash Flow to Firm, 5yr explicit + terminal',
            'Dividend Discount Model (Gordon Growth)',
            'Earnings × Conservative 15x Multiple'
        ]
    }
    
    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
    
    # === SENSITIVITY ANALYSIS ===
    st.markdown("---")
    st.subheader("📊 Sensitivity Analysis: WACC vs Terminal Growth")
    
    # Create sensitivity matrix
    wacc_range = np.linspace(wacc - 0.02, wacc + 0.02, 9)
    tg_range = np.linspace(t_growth - 0.01, t_growth + 0.01, 9)
    
    matrix = np.zeros((len(wacc_range), len(tg_range)))
    
    with st.spinner("Computing sensitivity matrix..."):
        for i, w in enumerate(wacc_range):
            for j, g in enumerate(tg_range):
                if w <= g:
                    matrix[i, j] = np.nan
                else:
                    res = run_multi_valuation(inputs, growth_rate, w, g, market_data)
                    matrix[i, j] = res['dcf_price']
    
    # Plot heatmap
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f"{g*100:.2f}%" for g in tg_range],
        y=[f"{w*100:.2f}%" for w in wacc_range],
        colorscale='RdYlGn',
        name='Price ($)',
        hovertemplate='WACC: %{y}<br>Terminal G: %{x}<br>Price: $%{z:.2f}<extra></extra>'
    ))
    
    fig_heatmap.update_layout(
        title="DCF Price Sensitivity: WACC vs Terminal Growth",
        xaxis_title="Terminal Growth Rate",
        yaxis_title="WACC",
        height=500,
        hovermode='closest'
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # === INVESTMENT RECOMMENDATION ===
    st.markdown("---")
    st.subheader("🎯 Investment Perspective")
    
    if upside_pct > 20:
        st.success(f"✅ **BUY**: Stock trading at significant discount ({upside_pct:.1f}% upside)")
    elif upside_pct > 5:
        st.info(f"🟡 **HOLD**: Stock trading near fair value ({upside_pct:.1f}% upside)")
    elif upside_pct > -5:
        st.warning(f"🟡 **HOLD**: Stock trading near fair value ({upside_pct:.1f}%)")
    else:
        st.error(f"❌ **SELL**: Stock trading at premium ({upside_pct:.1f}% downside)")
    
    # Show assumptions transparency
    with st.expander("📝 Valuation Assumptions & Sensitivity", expanded=False):
        st.write("""
        **Key Model Assumptions:**
        - **Forecast Period:** 5 years with constant EBIT margin
        - **Terminal Growth:** Perpetuity growth at specified rate
        - **Tax Rate:** 21% (US federal corporate tax rate)
        - **Risk-Free Rate:** 4.5% (10-year UST reference)
        - **Equity Risk Premium:** 5.5% (market historical average)
        
        **Sensitivity Interpretation:**
        - If valuation drops significantly with small WACC increase → Value concentrated in terminal value
        - If valuation sensitive to terminal growth → Model vulnerable to long-term assumptions
        - Ideal position: Valuation stable across reasonable assumption ranges
        """)


def render_sensitivity_analysis(ticker: str, growth_rate: float, 
                               wacc: float, t_growth: float) -> None:
    """Comprehensive sensitivity analysis section"""
    
    st.subheader("📊 Advanced Sensitivity Analysis")
    
    # Fetch data
    fetcher = SECDataFetcher(ticker)
    inputs = fetcher.get_valuation_inputs()
    
    if inputs is None:
        st.error(f"Cannot fetch data for {ticker}")
        return
    
    # Market data
    market_data = {'rf': 0.045, 'erp': 0.055}
    
    col1, col2 = st.columns(2)
    
    with col1:
        wacc_min = st.slider("WACC Min (%)", 4.0, 8.0, max(4.0, wacc - 0.02) * 100) / 100
        wacc_max = st.slider("WACC Max (%)", 8.0, 15.0, min(15.0, wacc + 0.02) * 100) / 100
    
    with col2:
        tg_min = st.slider("Terminal Growth Min (%)", 0.5, 2.5, max(0.5, t_growth - 0.01) * 100) / 100
        tg_max = st.slider("Terminal Growth Max (%)", 2.5, 5.0, min(5.0, t_growth + 0.01) * 100) / 100
    
    # Generate matrix
    wacc_range = np.linspace(wacc_min, wacc_max, 11)
    tg_range = np.linspace(tg_min, tg_max, 11)
    
    matrix = np.zeros((len(wacc_range), len(tg_range)))
    
    with st.spinner("Computing sensitivity matrix..."):
        for i, w in enumerate(wacc_range):
            for j, g in enumerate(tg_range):
                if w <= g:
                    matrix[i, j] = np.nan
                else:
                    try:
                        res = run_multi_valuation(inputs, growth_rate, w, g, market_data)
                        matrix[i, j] = res['dcf_price']
                    except:
                        matrix[i, j] = np.nan
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=[f"{g*100:.2f}%" for g in tg_range],
        y=[f"{w*100:.2f}%" for w in wacc_range],
        colorscale='RdYlGn',
        hovertemplate='WACC: %{y}<br>Term Growth: %{x}<br>Price: $%{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Price Sensitivity Analysis: {ticker}",
        xaxis_title="Terminal Growth Rate",
        yaxis_title="WACC",
        height=600,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_qa_section() -> None:
    """Educational Q&A masterclass"""
    
    st.subheader("❓ Valuation Q&A Masterclass")
    st.write("A comprehensive guide to DCF valuation concepts and terminology.")
    
    for question, answer in VALUATION_QA:
        with st.expander(question, expanded=False):
            st.write(answer)


def render_about_section() -> None:
    """About and methodology section"""
    
    st.subheader("ℹ️ About This Terminal")
    
    st.write(ABOUT_CONTENT['intro'])
    
    st.markdown("---")
    st.subheader("🛠️ The Institutional Valuation Workflow")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(ABOUT_CONTENT['workflow'])
    
    with col2:
        st.markdown("""
        **Key Features:**
        - ✅ Audited SEC data (10-K)
        - ✅ Two-stage FCFF model
        - ✅ Sensitivity analysis
        - ✅ Institutional branding
        - ✅ Educational content
        """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Stage 1 (Explicit):**")
        st.write(ABOUT_CONTENT['arima'])
    
    with col2:
        st.markdown("**WACC Discount:**")
        st.write(ABOUT_CONTENT['vasicek'])
    
    with col3:
        st.markdown("**Terminal Assumption:**")
        st.write(ABOUT_CONTENT['cir'])


def main():
    """Main application orchestrator"""
    
    # Header
    header_component()
    
    # Sidebar inputs
    sidebar_result = sidebar_component()
    
    if sidebar_result is None:
        st.warning("⚠️ Please fix parameter errors in sidebar to continue")
        return
    
    ticker, growth_rate, wacc, t_growth, run_val = sidebar_result
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Valuation Analysis", "📈 Sensitivity", "❓ Q&A", "ℹ️ About"]
    )
    
    with tab1:
        if run_val:
            render_valuation_analysis(ticker, growth_rate, wacc, t_growth)
        else:
            st.info("👈 Click 'EXECUTE AUDITED DCF' in sidebar to run valuation")
    
    with tab2:
        if run_val:
            render_sensitivity_analysis(ticker, growth_rate, wacc, t_growth)
        else:
            st.info("👈 Click 'EXECUTE AUDITED DCF' in sidebar first")
    
    with tab3:
        render_qa_section()
    
    with tab4:
        render_about_section()
    
    # Footer
    footer_component()


if __name__ == "__main__":
    main()
