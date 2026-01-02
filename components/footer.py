import streamlit as st
from datetime import datetime

def footer_component():
    """Redesigned professional footer with social links"""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <h4 style="color: #002147; margin-bottom: 10px;">THE MOUNTAIN PATH - WORLD OF FINANCE</h4>
                <div style="display: flex; justify-content: center; gap: 15px; margin-bottom: 15px;">
                    <a href="https://www.linkedin.com/in/trichyravis" target="_blank">
                        <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white">
                    </a>
                    <a href="https://github.com/trichyravis" target="_blank">
                        <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white">
                    </a>
                </div>
                <p style="color: #666; font-size: 0.8rem; line-height: 1.4;">
                    <strong>DISCLAIMER:</strong> This terminal is for educational purposes only. 
                    Calculations are based on automated SEC data retrieval and user-defined assumptions. 
                    Past performance is not indicative of future results.
                </p>
                <p style="color: #999; font-size: 0.7rem; margin-top: 15px;">
                    © {datetime.now().year} Prof. V. Ravichandran | Last Updated: {datetime.now().strftime("%Y-%m-%d")}
                </p>
            </div>
        """, unsafe_allow_html=True)
