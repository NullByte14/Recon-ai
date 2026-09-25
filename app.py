import streamlit as st
import pandas as pd
import os
from matcher import reconcile
from ai_summary import generate_summary

# Configure page
st.set_page_config(
    page_title="ReconAI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
    <style>
    /* Hide the Streamlit header, menu, and print/record options */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        background-color: #4CAF50;
        color: white;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

# Data Loading State
if 'ledger_df' not in st.session_state:
    st.session_state.ledger_df = None
if 'bank_df' not in st.session_state:
    st.session_state.bank_df = None
if 'reconciled' not in st.session_state:
    st.session_state.reconciled = False
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'summary_stats' not in st.session_state:
    st.session_state.summary_stats = None
if 'last_ledger_name' not in st.session_state:
    st.session_state.last_ledger_name = None
if 'last_bank_name' not in st.session_state:
    st.session_state.last_bank_name = None



# Main Title
st.title("ReconAI — AI-Powered Financial Reconciliation")
st.markdown("##### Upload your ledger and bank statement to automatically detect and explain discrepancies")
st.markdown("---")

# File Uploads
col1, col2 = st.columns(2)

with col1:
    ledger_file = st.file_uploader("Upload Ledger CSV", type=['csv'])

with col2:
    bank_file = st.file_uploader("Upload Bank Statement CSV", type=['csv'])

# Handle file uploads (only reset state if a new file is uploaded)
try:
    if ledger_file is not None and ledger_file.name != st.session_state.last_ledger_name:
        st.session_state.ledger_df = pd.read_csv(ledger_file)
        st.session_state.last_ledger_name = ledger_file.name
        st.session_state.reconciled = False
        
    if bank_file is not None and bank_file.name != st.session_state.last_bank_name:
        st.session_state.bank_df = pd.read_csv(bank_file)
        st.session_state.last_bank_name = bank_file.name
        st.session_state.reconciled = False
except Exception as e:
    st.error(f"Error reading CSV files. Please ensure they are valid. ({e})")

# Testing Options (moved from sidebar)
with st.expander("🧪 Testing Options (Load Sample Data)"):
    st.info("Use this to quickly load sample data if you don't have your own CSV files.")
    if st.button("Load Sample Data"):
        try:
            if not os.path.exists('data/ledger_sample.csv') or not os.path.exists('data/bank_statement_sample.csv'):
                st.error("Sample data not found. Please run `python generate_sample_data.py` first.")
            else:
                st.session_state.ledger_df = pd.read_csv('data/ledger_sample.csv')
                st.session_state.bank_df = pd.read_csv('data/bank_statement_sample.csv')
                st.session_state.reconciled = False
                st.success("Sample data loaded! Click 'Run Reconciliation' below.")
        except Exception as e:
            st.error(f"Error loading sample data: {e}")

# Submit button for reconciliation
if st.session_state.ledger_df is not None and st.session_state.bank_df is not None:
    if st.button("Run Reconciliation", type="primary"):
        with st.spinner("Reconciling transactions..."):
            try:
                results_df, summary_stats = reconcile(st.session_state.ledger_df, st.session_state.bank_df)
                st.session_state.results_df = results_df
                st.session_state.summary_stats = summary_stats
                st.session_state.reconciled = True
            except Exception as e:
                st.error(f"Error during reconciliation: {e}")

# Display Results
if st.session_state.reconciled and st.session_state.results_df is not None:
    st.markdown("### Reconciliation Summary")
    
    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    stats = st.session_state.summary_stats
    m1.metric("Total Transactions", stats["Total Transactions"])
    m2.metric("Matched cleanly", stats["Matched"])
    m3.metric("Flagged Issues", stats["Flagged"])
    m4.metric("Total Discrepancy Value", f"₹{stats['Total Discrepancy Value (₹)']:,}")
    
    st.markdown("---")
    st.markdown("### Transaction Details")
    
    # Styling function for pandas
    def highlight_status(val):
        color = ''
        if val == 'Matched':
            color = 'background-color: rgba(76, 175, 80, 0.2)' # Green
        elif val == 'Timing Difference':
            color = 'background-color: rgba(255, 193, 7, 0.2)' # Yellow
        elif val in ['Unmatched - Ledger Only', 'Unmatched - Bank Only', 'Amount Mismatch', 'Possible Duplicate']:
            color = 'background-color: rgba(244, 67, 54, 0.2)' # Red
        return color

    # Apply styling
    styled_df = st.session_state.results_df.style.map(
        highlight_status, subset=['status']
    ).format({'amount': '₹{:.2f}'}, na_rep="")
    
    # Show dataframe
    st.dataframe(styled_df, width='stretch', height=400)
    
    st.markdown("---")
    
    # AI Summary Section
    st.markdown("### AI Executive Summary")
    st.markdown("Generate an AI-powered explanation of the discrepancies and suggested next steps.")
    
    if st.button("Generate AI Summary"):
        flagged_df = st.session_state.results_df[st.session_state.results_df['status'] != 'Matched']
        
        if flagged_df.empty:
            st.success("No discrepancies found! All transactions match perfectly. No summary needed.")
        else:
            with st.spinner("Analyzing discrepancies with AI..."):
                summary_markdown = generate_summary(flagged_df)
                
            st.markdown("""
            <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333;">
            """, unsafe_allow_html=True)
            st.markdown(summary_markdown)
            st.markdown("</div>", unsafe_allow_html=True)
