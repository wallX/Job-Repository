# views/list_view.py
import pandas as pd
import streamlit as st
from urllib.parse import urlparse

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import db

# Status options and associated color mappings
STATUS_OPTIONS = ["Not Applied", "Applied", "Rejected", "Ghosted", "Accepted"]

STATUS_COLORS = {
    "Not Applied": {"bg": "#e2e8f0", "text": "#475569", "border": "#cbd5e1"}, # Gray
    "Applied":     {"bg": "#ffedd5", "text": "#c2410c", "border": "#fdba74"}, # Orange
    "Rejected":    {"bg": "#fee2e2", "text": "#b91c1c", "border": "#fca5a5"}, # Red
    "Ghosted":     {"bg": "#f3e8ff", "text": "#6b21a8", "border": "#d8b4fe"}, # Purple
    "Accepted":    {"bg": "#dcfce7", "text": "#15803d", "border": "#86efac"}, # Green
}
def render_status_badge_html(status: str) -> str:
    """Generates styled HTML badge without excess bottom/top margin."""
    s = status if status in STATUS_COLORS else "Not Applied"
    style = STATUS_COLORS[s]
    return (
        f'<span style="background-color: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 3px 10px; border-radius: 12px; '
        f'font-size: 0.8rem; font-weight: 600; white-space: nowrap; display: inline-block; '
        f'margin-top: 4px; margin-bottom: 0px;">{s}</span>'
    )

def on_status_change(job_id: str, selectbox_key: str):
    """Callback triggered when the status dropdown changes directly on a card."""
    new_status = st.session_state[selectbox_key]
    db.update_job_application_data(job_id=job_id, application_status=new_status)
    st.toast(f"Updated status to '{new_status}'")


@st.dialog("📋 Full Job Details & Application Notes", width="large")
def show_job_details_dialog(job: pd.Series):
    """Modal details view with application status dropdown and updatable notes."""
    job_id = str(job.get("job_id"))
    title = job.get("title") or "Untitled Job"
    company = job.get("company") or "Unknown Company"
    
    st.subheader(f"{title} @ {company}")
    
    if job.get("url"):
        st.link_button("🌐 View Original Job Posting", job["url"])

    st.divider()

    # --- EDITABLE APPLICATION SECTION ---
    st.markdown("### 📝 Application Tracking")
    
    current_status = job.get("application_status") or "Not Applied"
    if current_status not in STATUS_OPTIONS:
        current_status = "Not Applied"
        
    current_notes = job.get("application_notes") or ""

    with st.form(f"dialog_app_form_{job_id}"):
        col_status, col_empty = st.columns([1, 1])
        with col_status:
            new_status = st.selectbox(
                "Application Status",
                options=STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status),
                key=f"dialog_status_{job_id}"
            )

        new_notes = st.text_area(
            "Application Notes",
            value=current_notes,
            placeholder="e.g. Applied via referral on LinkedIn. Interview scheduled for Tuesday...",
            height=110,
            key=f"dialog_notes_{job_id}"
        )

        save_btn = st.form_submit_button("💾 Save Application Details", use_container_width=True)
        if save_btn:
            db.update_job_application_data(
                job_id=job_id, 
                application_status=new_status, 
                application_notes=new_notes
            )
            st.success("✅ Application status and notes updated!")
            st.rerun()

    st.divider()

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pipeline Status", str(job.get("status", "N/A")))
    m2.metric("Junior Friendly", "YES" if job.get("is_junior") == 1 else "NO")
    
    j_score = job.get("junior_score")
    m3.metric("Junior Score", f"{j_score:.1f}/10" if pd.notna(j_score) else "N/A")
    m4.metric("Work Model", str(job.get("work_model") or "N/A"))

    # LLM Summary
    st.markdown("### 🤖 LLM Summary")
    summary = job.get("llm_summary")
    if pd.notna(summary) and str(summary).strip():
        st.info(str(summary))
    else:
        st.caption("Pending LLM analysis...")

    # Stack Gaps
    gap = job.get("stack_gap")
    if pd.notna(gap) and str(gap).strip():
        st.warning(f"**Tech Stack Gaps:** {gap}")

    # Full Description
    with st.expander("📄 Full Scraped Description"):
        desc = job.get("full_description")
        st.write(str(desc) if pd.notna(desc) else "No raw text available.")


def render_job_card(job: pd.Series):
    """Renders a single job offer card with compact action buttons and application status dropdown."""
    
    def clean_str(val, default="N/A"):
        if pd.notna(val) and str(val).strip():
            return str(val).strip()
        return default

    # 1. Company Logo via company_image_url with URL validation
    company_image_url = clean_str(job.get("company_image_url"), default="")

    def is_valid_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme in ("http", "https") and parsed.netloc)
        except Exception:
            return False

    if is_valid_url(company_image_url):
        company_logo_html = f'<img src="{company_image_url}" style="width: 36px; height: 36px; border-radius: 6px; margin-right: 12px; vertical-align: middle;" alt="logo">'
    else:
        company_logo_html = "🏢 "

    source_name = clean_str(job.get("source"), default="N/A")
    if source_name != "N/A":
        source_domain = source_name.lower().replace(" ", "")
        if "." not in source_domain:
            source_domain = f"{source_domain}.com"
        favicon_url = f"https://www.google.com/s2/favicons?domain={source_domain}&sz=64"
        source_icon_html = f'<img src="{favicon_url}" style="width: 16px; height: 16px; margin-right: 4px; vertical-align: middle;" alt="source">'
    else:
        source_icon_html = "🌐 "

    # 2. Field Fallbacks
    title = clean_str(job.get("title"), "Untitled Position")
    company = clean_str(job.get("company"), "Unknown Company")
    location = clean_str(job.get("location") or job.get("city"), "Not specified")
    work_model = clean_str(job.get("work_model"), "N/A")
    workload = clean_str(job.get("workload"), "N/A")
    contract_type = clean_str(job.get("contract_type"), "N/A")
    
    raw_pub_date = job.get("publication_date") or job.get("added_at")
    pub_date = clean_str(raw_pub_date, "N/A")[:10]

    language = job.get("language_llm")
    if isinstance(language, list):
        language = ", ".join(language)
    else:
        language = clean_str(language, "N/A")

    company_url = clean_str(job.get("url"), default="")
    job_id = str(job.get("job_id"))

    # Application Status
    app_status = clean_str(job.get("application_status"), default="Not Applied")
    if app_status not in STATUS_OPTIONS:
        app_status = "Not Applied"

    # 3. Card Container
    with st.container(key=f"job_card_{job_id}", border=True):
        col_header, col_status_select, col_actions,  = st.columns([2.8, 1.8, 1.4], vertical_alignment="top")

        with col_header:
            # 1. Title
            st.markdown(
                f'<h3 style="margin: 0; padding: 0; line-height: 1.2;">{company_logo_html} {title}</h3>', 
                unsafe_allow_html=True
            )
            
            # 2. Company & Source
            st.markdown(
                f'<div style="margin-top: 4px; margin-bottom: 2px;">'
                f'<strong>{company}</strong> &nbsp;|&nbsp; {source_icon_html} <em>Source:</em> <code>{source_name}</code>'
                f'</div>',
                unsafe_allow_html=True
            )

            # 3. Status Badge Underneath
            st.markdown(render_status_badge_html(app_status), unsafe_allow_html=True)

        #with col_status_select:
        #    # Dropdown right on the card for instant status updates
        #    sb_key = f"card_app_status_{job_id}"
        #    st.selectbox(
        #        "Application Status",
        #        options=STATUS_OPTIONS,
        #        index=STATUS_OPTIONS.index(app_status),
        #        key=sb_key,
        #        on_change=on_status_change,
        #        args=(job_id, sb_key),
        #        label_visibility="collapsed"
        #    )

        with col_actions:
            # Reduced button sizes using custom column alignment
            btn_c1, btn_c2 = st.columns(2)
            
            with btn_c1:
                # Triggers the Streamlit Modal
                if st.button("Details", key=f"details_{job_id}", use_container_width=True):
                    show_job_details_dialog(job)

            with btn_c2:
                # Compact Open Offer Link Button
                if company_url:
                    st.link_button("Offer", company_url, use_container_width=True)

        st.divider()

        # Row 1: Location, Work Model, Workload, Contract Type
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"📍 **Location:**\n{location}")
        c2.markdown(f"🏠 **Work Model:**\n{work_model}")
        c3.markdown(f"⏱️ **Workload:**\n{workload}")
        c4.markdown(f"📜 **Contract Type:**\n{contract_type}")

        st.write("") 

        # Row 2: Publication Date & Language
        c5, c6 = st.columns(2)
        c5.markdown(f"📅 **Published:**\n{pub_date}")
        c6.markdown(f"🗣️ **Language:**\n{language}")


def render_list_view():
    """Renders the job offers as visual cards with filtering."""
    st.subheader("All Job Offers")

    df = db.load_jobs_df()

    if df.empty:
        st.info("No jobs found in database. Use the 'Ingest New Offer' tab to add some!")
        return

    # =========================================================
    # 🔍 FILTER BAR
    # =========================================================
    with st.expander("🔍 Filter Options", expanded=True):
        col_search, col_app_status, col_tags, col_junior = st.columns([3, 2, 2, 2])

        with col_search:
            search_query = st.text_input("Search Keywords", placeholder="Title, company, stack...", key="card_search")

        with col_app_status:
            selected_app_statuses = st.multiselect(
                "App Status", 
                STATUS_OPTIONS, 
                default=STATUS_OPTIONS, 
                key="card_app_status"
            )

        with col_tags:
            all_tags = set()
            for row in df["search_term"].dropna():
                all_tags.update([t.strip() for t in row.split(",") if t.strip()])
            selected_tags = st.multiselect("Search Terms", sorted(list(all_tags)), key="card_tags")

        with col_junior:
            st.write(" ")
            junior_only = st.checkbox("Junior Only", value=False, key="card_junior")

    # =========================================================
    # 🎯 APPLY FILTERS
    # =========================================================
    filtered_df = df.copy()

    if "application_status" in filtered_df.columns and selected_app_statuses:
        filtered_df["temp_app_status"] = filtered_df["application_status"].fillna("Not Applied")
        filtered_df = filtered_df[filtered_df["temp_app_status"].isin(selected_app_statuses)]

    if junior_only and "is_junior" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["is_junior"] == 1]

    if selected_tags and "search_term" in filtered_df.columns:
        pattern = "|".join(selected_tags)
        filtered_df = filtered_df[filtered_df["search_term"].str.contains(pattern, case=False, na=False)]

    if search_query:
        query = search_query.lower()
        title_match = filtered_df["title"].str.lower().str.contains(query, na=False) if "title" in filtered_df else False
        company_match = filtered_df["company"].str.lower().str.contains(query, na=False) if "company" in filtered_df else False
        summary_match = filtered_df["llm_summary"].str.lower().str.contains(query, na=False) if "llm_summary" in filtered_df else False
        filtered_df = filtered_df[title_match | company_match | summary_match]

    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** job offers")

    print(f"table header: {list(filtered_df.columns)}")

    # =========================================================
    # 🎴 CARDS LISTING
    # =========================================================
    for idx, job in filtered_df.iterrows():
        render_job_card(job)