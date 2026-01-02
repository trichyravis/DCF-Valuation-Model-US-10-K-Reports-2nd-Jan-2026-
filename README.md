
# 🏔️ The Mountain Path: Institutional Equity Valuation Terminal
**Advanced Two-Stage FCFF Model with Automated SEC Data Integration**

---

## 🏛️ Project Overview
The **Mountain Path Valuation Terminal** is a professional-grade quantitative tool designed to estimate the intrinsic value of US-listed corporations. Unlike static models, this terminal automates the extraction of audited financial data directly from **SEC 10-K filings**, eliminating transcription errors and providing a real-time "Margin of Safety" analysis.

Designed by **Prof. V. Ravichandran**, this platform bridges the gap between academic financial theory and institutional equity research practice.

---

## 🚀 Key Features
* **Automated SEC Retrieval:** Real-time fetching of Total Revenue, EBIT, Net Debt, and Shares Outstanding via `yfinance` API.
* **Two-Stage FCFF Engine:** * **Stage 1:** 5-year explicit forecast period with adjustable revenue growth and operating margins.
    * **Stage 2:** Terminal Value calculation using the Gordon Growth (Perpetuity) method.
* **Bivariate Sensitivity Analysis:** Interactive heatmap visualizing Enterprise Value (EV) fluctuations across varying WACC and Terminal Growth regimes.
* **Educational Masterclass:** Integrated Q&A module covering 15+ complex valuation topics for pedagogical excellence.
* **Institutional Branding:** High-fidelity UI using Oxford Blue (#002147) and Gold (#FFD700) design standards.

---

## 🛠️ Repository Structure
The project follows a modular architecture to ensure scalability and maintainability:

```text
mountain-path-valuation/
├── .streamlit/          # Configuration and Oxford Blue/Gold branding
├── assets/              # Branding assets (logo.png)
├── components/          # UI Modules (Header, Sidebar, Footer)
├── content/             # Methodology and Masterclass Q&A text
├── modules/             # Core Quantitative Engines (SEC Fetcher, DCF Engine)
├── reports/             # Archive for generated valuation CSVs
├── app.py               # Main Application Orchestrator
└── requirements.txt     # Python dependencies
