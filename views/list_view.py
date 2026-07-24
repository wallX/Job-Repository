# views/list_view.py
import pandas as pd
import streamlit as st
from urllib.parse import urlparse
import unicodedata

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import db


def normalize_text(text: str) -> str:
    """
    Normalizes text by converting to lowercase, removing accents/diacritics 
    (e.g., 'Zürich' -> 'zurich'), and stripping non-alphanumeric characters.
    """
    if not text or pd.isna(text):
        return ""
    
    # 1. Convert to string and lowercase
    text = str(text).lower()
    
    # 2. Separate characters and combining accents (NFKD form)
    nfkd_form = unicodedata.normalize('NFKD', text)
    
    # 3. Keep base characters, discarding accent markers (e.g., 'ü' -> 'u')
    base_text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # 4. Replace non-alphanumeric characters with spaces (strips punctuation)
    cleaned = "".join([c if c.isalnum() else " " for c in base_text])
    
    # 5. Normalize whitespace
    return " ".join(cleaned.split())

# Status options and associated color mappings
STATUS_OPTIONS = ["Not Applied", "Applied", "Rejected", "Ghosted", "Interviewing", "Accepted"]

STATUS_COLORS = {
    "Not Applied": {"bg": "#e2e8f0", "text": "#475569", "border": "#cbd5e1"}, # Gray
    "Applied":     {"bg": "#ffedd5", "text": "#c2410c", "border": "#fdba74"}, # Orange
    "Rejected":    {"bg": "#fee2e2", "text": "#b91c1c", "border": "#fca5a5"}, # Red
    "Ghosted":     {"bg": "#f3e8ff", "text": "#6b21a8", "border": "#d8b4fe"}, # Purple
    "Interviewing": {"bg": "#e0f2fe", "text": "#0369a1", "border": "#7dd3fc"}, # Blue
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


@st.dialog("Full Job Details & Application Notes", width="large")
def show_job_details_dialog(job: pd.Series):
    """Modal details view with application status dropdown, notes, and LLM foreign-friendliness metrics."""
    job_id = str(job.get("job_id"))
    title = job.get("title") or "Untitled Job"
    company = job.get("company") or "Unknown Company"
    
    st.subheader(f"{title} @ {company}")
    
    # --- HEADER LINK & BADGE ROW ---
    current_status = job.get("application_status") or "Not Applied"
    if current_status not in STATUS_OPTIONS:
        current_status = "Not Applied"

    # Use numeric ratios: tight space for button & badge, remaining space absorbed by spacer
    col_link, col_badge, _ = st.columns([1.2, 1, 8], vertical_alignment="center")
    
    with col_link:
        if job.get("url"):
            st.link_button("🌐 View Original Job Posting", job["url"])
            
    with col_badge:
        st.markdown(render_status_badge_html(current_status), unsafe_allow_html=True)

    st.divider()

    # --- EDITABLE APPLICATION TRACKING (EXPANDER DROPDOWN) ---
    with st.expander("📝 Application Tracking & Notes", expanded=False):
        current_notes = job.get("application_notes") or ""

        with st.form(f"dialog_app_form_{job_id}"):
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

    # --- METRICS GRID ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pipeline Status", str(job.get("status", "N/A")))
    m2.metric("Junior Friendly", "YES" if job.get("is_junior") == 1 else "NO")
    
    j_score = job.get("junior_score")
    m3.metric("Junior Score", f"{j_score:.1f}/10" if pd.notna(j_score) else "N/A")
    
    ff_score = job.get("foreign_friendly_score")
    m4.metric("Foreign Score", f"{ff_score:.1f}/10" if pd.notna(ff_score) else "N/A")

    # --- LLM TAGS & FOREIGN FRIENDLY REASONS ---
    st.markdown("### 🌍 Foreign Friendliness & Stack Insights")
    
    ff_reasons = job.get("foreign_friendly_reasons")
    if pd.notna(ff_reasons) and str(ff_reasons).strip():
        st.info(f"**Foreign Friendliness Assessment:**\n{ff_reasons}")
    else:
        st.caption("No foreign friendliness evaluation recorded.")

    llm_tags = job.get("llm_tags")
    if pd.notna(llm_tags) and str(llm_tags).strip():
        if isinstance(llm_tags, list):
            tags_str = ", ".join(llm_tags)
        else:
            tags_str = str(llm_tags)
        st.markdown(f"🏷️ **LLM Generated Tags:** `{tags_str}`")

    # --- LLM SUMMARY & STACK GAPS ---
    st.markdown("### 🤖 LLM Summary")
    summary = job.get("llm_summary")
    if pd.notna(summary) and str(summary).strip():
        st.write(str(summary))
    else:
        st.caption("Pending LLM analysis...")

    gap = job.get("stack_gap")
    if pd.notna(gap) and str(gap).strip():
        st.warning(f"**Tech Stack Gaps:** {gap}")

    # --- FULL DESCRIPTION ---
    with st.expander("📄 Full Scraped Description"):
        desc = job.get("full_description")
        st.write(str(desc) if pd.notna(desc) else "No raw text available.")


def render_job_card(job: pd.Series):
    """Renders a single job offer card with compact action buttons and aligned metadata."""
    
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

    # Tags & Metrics Processing
    search_terms_raw = clean_str(job.get("search_term"), default="")
    search_terms = [t.strip() for t in search_terms_raw.split(",") if t.strip()] if search_terms_raw != "N/A" else []

    llm_tags_raw = job.get("llm_tags")
    if isinstance(llm_tags_raw, list):
        llm_tags = [str(t).strip() for t in llm_tags_raw if str(t).strip()]
    elif pd.notna(llm_tags_raw) and str(llm_tags_raw).strip():
        llm_tags = [t.strip() for t in str(llm_tags_raw).split(",") if t.strip()]
    else:
        llm_tags = []

    is_junior_val = job.get("is_junior")
    junior_friendly_str = "🟢 YES" if is_junior_val == 1 or is_junior_val is True else "🔴 NO"

    yoe_val = job.get("required_yoe")
    required_yoe_str = f"{yoe_val} yrs" if pd.notna(yoe_val) and str(yoe_val).strip() else "N/A"

    ff_score = job.get("foreign_friendly_score")
    ff_score_str = f"{ff_score:.1f}/10" if pd.notna(ff_score) else "N/A"

    # Application Status
    app_status = clean_str(job.get("application_status"), default="Not Applied")
    if app_status not in STATUS_OPTIONS:
        app_status = "Not Applied"

    # 3. Card Container
    with st.container(key=f"job_card_{job_id}", border=True):
        col_header, col_actions = st.columns([4, 1.2], vertical_alignment="top")

        with col_header:
            # Title
            st.markdown(
                f'<h3 style="margin: 0; padding: 0; line-height: 1.2;">{company_logo_html} {title}</h3>', 
                unsafe_allow_html=True
            )
            
            # Company & Source
            st.markdown(
                f'<div style="margin-top: 4px; margin-bottom: 2px;">'
                f'<strong>{company}</strong> &nbsp;|&nbsp; {source_icon_html} <em>Source:</em> <code>{source_name}</code>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Status Badge Underneath
            st.markdown(render_status_badge_html(app_status), unsafe_allow_html=True)

        with col_actions:
            btn_c1, btn_c2 = st.columns(2)
            
            with btn_c1:
                if st.button("Details", key=f"details_{job_id}", use_container_width=True):
                    show_job_details_dialog(job)

            with btn_c2:
                if company_url:
                    st.link_button("Offer", company_url, use_container_width=True)

        st.divider()

        # Tags Section (Search terms & LLM tags)
        if search_terms or llm_tags:
            tags_html = ""
            for term in search_terms:
                tags_html += f'<span style="background-color: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; margin-right: 4px; display: inline-block; margin-bottom: 4px;">🔍 {term}</span>'
            for tag in llm_tags:
                tags_html += f'<span style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 500; margin-right: 4px; display: inline-block; margin-bottom: 4px;">🏷️ {tag}</span>'
            
            st.markdown(f'<div style="margin-bottom: 10px;">{tags_html}</div>', unsafe_allow_html=True)

        # Row 1: Core Job Conditions
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"📍 **Location:**\n{location}")
        c2.markdown(f"🏠 **Work Model:**\n{work_model}")
        c3.markdown(f"⏱️ **Workload:**\n{workload}")
        c4.markdown(f"📜 **Contract:**\n{contract_type}")

        # Row 2: Candidate Match & Post Info
        c5, c6, c7, c8 = st.columns(4)
        c5.markdown(f"🎓 **Junior:**\n{junior_friendly_str}")
        c6.markdown(f"⏳ **YoE:**\n{required_yoe_str}")
        c7.markdown(f"🌍 **Foreign Score:**\n{ff_score_str}")
        c8.markdown(f"📅 **Published:**\n{pub_date} *({language})*")

def render_list_view():
    """Renders job offers as visual cards with sidebar filtering."""
    
    df = db.load_jobs_df()

    if df.empty:
        st.subheader("All Job Offers")
        st.info("No jobs found in database. Use the 'Ingest New Offer' tab to add some!")
        return

    # =========================================================
    # 👈 SIDEBAR FILTER NAVIGATION
    # =========================================================
    st.sidebar.header("🔍 Filter Job Offers")

    # 1. Broad Search Input (ID, Title, Company, Stack, Summary)
    search_query = st.sidebar.text_input(
        "Keyword Search", 
        placeholder="ID, Title, Company, Stack...", 
        key="sidebar_search"
    )

    # 2. Application Status Multiselect
    selected_app_statuses = st.sidebar.multiselect(
        "Application Status", 
        options=STATUS_OPTIONS, 
        default=STATUS_OPTIONS, 
        key="sidebar_app_status"
    )

    # 3. Dynamic Location Filter
    all_locations = set()
    for row in df["location"].fillna(df["city"]).dropna():
        # Split on commas or slashes if multiple locations exist in one string
        for loc in str(row).split(","):
            cleaned = loc.strip()
            if cleaned and cleaned.lower() != "n/a":
                all_locations.add(cleaned)

    selected_locations = st.sidebar.multiselect(
        "Locations / Cities", 
        options=sorted(list(all_locations)), 
        key="sidebar_locations"
    )

    # 4. Dynamic Search Terms Filter
    all_terms = set()
    for row in df["search_term"].dropna():
        all_terms.update([t.strip() for t in str(row).split(",") if t.strip()])

    selected_terms = st.sidebar.multiselect(
        "Search Terms / Query", 
        options=sorted(list(all_terms)), 
        key="sidebar_terms"
    )

    # 5. Checkbox Filters (Junior & Foreign Friendly)
    st.sidebar.divider()
    col_j, col_ff = st.sidebar.columns(2)
    with col_j:
        junior_only = st.checkbox("👶 Junior Only", value=False, key="sidebar_junior")
    with col_ff:
        foreign_only = st.checkbox("🌍 Foreign Friendly", value=False, key="sidebar_foreign")


    # =========================================================
    # 🎯 APPLY FILTERS
    # =========================================================
    filtered_df = df.copy()

    # Application Status Filter
    if "application_status" in filtered_df.columns and selected_app_statuses:
        filtered_df["temp_app_status"] = filtered_df["application_status"].fillna("Not Applied")
        filtered_df = filtered_df[filtered_df["temp_app_status"].isin(selected_app_statuses)]

    # Junior Only Filter
    if junior_only and "is_junior" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["is_junior"] == 1]

    # Foreign Friendly Filter (Score >= 7 or English only)
    if foreign_only:
        ff_condition = pd.Series(False, index=filtered_df.index)
        if "foreign_friendly_score" in filtered_df.columns:
            ff_condition |= filtered_df["foreign_friendly_score"] >= 7.0
        if "language_llm_only_english" in filtered_df.columns:
            ff_condition |= filtered_df["language_llm_only_english"] == 1
        filtered_df = filtered_df[ff_condition]

    # Location Filter
    if selected_locations and ("location" in filtered_df.columns or "city" in filtered_df.columns):
        loc_pattern = "|".join(selected_locations)
        loc_match = filtered_df["location"].astype(str).str.contains(loc_pattern, case=False, na=False)
        city_match = filtered_df["city"].astype(str).str.contains(loc_pattern, case=False, na=False)
        filtered_df = filtered_df[loc_match | city_match]

    # Search Terms Filter
    if selected_terms and "search_term" in filtered_df.columns:
        term_pattern = "|".join(selected_terms)
        filtered_df = filtered_df[filtered_df["search_term"].astype(str).str.contains(term_pattern, case=False, na=False)]

    if search_query:
        # Split search query into normalized individual tokens (words)
        query_tokens = normalize_text(search_query).split()

        if query_tokens:
            def matches_query(row: pd.Series) -> bool:
                # Combine all searchable fields into a single text blob
                fields_to_search = [
                    row.get("job_id"),
                    row.get("title"),
                    row.get("company"),
                    row.get("location"),
                    row.get("city"),
                    row.get("llm_summary"),
                    row.get("stack_gap"),
                    row.get("full_description"),
                    row.get("search_term"),
                    row.get("llm_tags")
                ]
                
                # Normalize the combined searchable text for this job offer
                searchable_text = normalize_text(" ".join([str(f) for f in fields_to_search if pd.notna(f)]))
                
                # Ensure ALL query tokens appear in the searchable text (order-independent)
                return all(token in searchable_text for token in query_tokens)

            # Apply fuzzy matching across all rows
            filtered_df = filtered_df[filtered_df.apply(matches_query, axis=1)]


    # =========================================================
    # 🎴 CARDS LISTING MAIN VIEW
    # =========================================================
    st.subheader("All Job Offers")
    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** job offers")

    for idx, job in filtered_df.iterrows():
        render_job_card(job)