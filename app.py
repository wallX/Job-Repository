import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path


#from views.list_view import render_list_view
from views.ingest_view import render_ingest_view
from views.list_view import render_list_view





st.set_page_config(
    page_title="Job Intelligence Hub",
    layout="wide"
)
st.title("Job Pipeline Dashboard")

st.markdown("""
<style>
    /* 1. Page Background (Light Soft Gray) */
    .stApp {
        background-color: #f1f5f9 !important;
    }

    /* 2. Target job card containers specifically via key prefix */
    div[class*="st-key-job_card_"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;  /* Darker slate border for contrast */
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05) !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
    }

    /* Hover elevation effect for job cards */
    div[class*="st-key-job_card_"]:hover {
        border-color: #64748b !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.12), 0 4px 6px -4px rgba(0, 0, 0, 0.08) !important;
    }

    /* 3. Filter Box Styling */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04) !important;
    }
</style>
""", unsafe_allow_html=True)



# --- TAB 1: LIST & FILTER ---


# Use segmented_control (or st.radio) for top tab-like navigation
active_tab = st.segmented_control(
    "Navigation", 
    ["All Jobs", "Ingest New Offer"], 
    default="All Jobs",
    label_visibility="collapsed"
)

# --- TAB 1: ALL JOBS ---
if active_tab == "All Jobs":
    # Sidebar filters will ONLY exist when this tab is active
    st.sidebar.divider()
    
    # Render all your sidebar filters here
    render_list_view()

# --- TAB 2: MANUAL INGEST ---
elif active_tab == "Ingest New Offer":
    # Sidebar stays completely clean!
    render_ingest_view()