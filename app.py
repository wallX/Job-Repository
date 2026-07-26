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