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



# --- TAB 1: LIST & FILTER ---
tab_list, tab_ingest = st.tabs(["All Jobs", "Ingest New Offer"])

with tab_list:
    render_list_view()

# --- TAB 2: MANUAL INGEST ---
with tab_ingest:
    render_ingest_view()