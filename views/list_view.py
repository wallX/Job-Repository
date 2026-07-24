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


@st.dialog("📋 Full Job Details & LLM Analysis", width="large")
def show_job_details_dialog(job: pd.Series):
    """Renders the detailed inspector modal when 'Open Details' is clicked."""
    title = job.get("title") or "Untitled Job"
    company = job.get("company") or "Unknown Company"
    
    st.subheader(f"{title} @ {company}")
    
    if job.get("url"):
        st.link_button("🌐 View Original Job Posting", job["url"])

    st.divider()

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", str(job.get("status", "N/A")))
    m2.metric("Junior Friendly", "YES" if job.get("is_junior") == 1 else "NO")
    
    j_score = job.get("junior_score")
    m3.metric("Junior Score", f"{j_score:.1f}/10" if pd.notna(j_score) else "N/A")
    m4.metric("Work Model", str(job.get("work_model") or "N/A"))

    # LLM Breakdown
    st.markdown("### 🤖 LLM Summary")
    summary = job.get("llm_summary")
    if pd.notna(summary) and str(summary).strip():
        st.info(str(summary))
    else:
        st.caption("Pending LLM analysis...")

    col_meta, col_gaps = st.columns(2)
    with col_meta:
        st.markdown("**Structured Metrics:**")
        st.json({
            "Job ID": job.get("job_id"),
            "Search Terms": job.get("search_term"),
            "Required Experience (YoE)": job.get("required_yoe"),
            "Language Friction": job.get("language_friction"),
            "Contract Type": job.get("contract_type"),
            "Workload": job.get("workload"),
        })

    with col_gaps:
        st.markdown("**Tech Stack Gaps / Requirements:**")
        gap = job.get("stack_gap")
        if pd.notna(gap) and str(gap).strip():
            st.warning(str(gap))
        else:
            st.success("No significant stack gaps identified.")

    # Full Text
    with st.expander("📄 Full Scraped Description"):
        desc = job.get("full_description")
        st.write(str(desc) if pd.notna(desc) else "No raw text available.")


def render_job_card(job: pd.Series):
    """Renders a single job offer card with compact action buttons."""
    
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

    # 3. Card Container
    with st.container(key=f"job_card_{job_id}", border=True):
        col_header, col_actions = st.columns([3, 2])

        with col_header:
            st.markdown(f"### {company_logo_html} {title}", unsafe_allow_html=True)
            st.markdown(
                f"**{company}** &nbsp;|&nbsp; {source_icon_html} *Source:* `{source_name}`",
                unsafe_allow_html=True
            )

        with col_actions:
            # Reduced button sizes using custom column alignment
            btn_c1, btn_c2 = st.columns(2)
            
            with btn_c1:
                # Triggers the Streamlit Modal
                if st.button("🔍 Details", key=f"details_{job_id}", use_container_width=True):
                    show_job_details_dialog(job)

            with btn_c2:
                # Compact Open Offer Link Button
                if company_url:
                    st.link_button("🚀 Offer", company_url, use_container_width=True)

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
        col_search, col_status, col_tags, col_junior = st.columns([3, 2, 2, 2])

        with col_search:
            search_query = st.text_input("Search Keywords", placeholder="Title, company, stack...", key="card_search")

        with col_status:
            all_statuses = sorted(list(df["status"].dropna().unique()))
            selected_statuses = st.multiselect("Status", all_statuses, default=all_statuses, key="card_status")

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

    if selected_statuses:
        filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]

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

    #print(f"table header: {list(filtered_df.columns)}")

    # =========================================================
    # 🎴 CARDS LISTING
    # =========================================================
    for idx, job in filtered_df.iterrows():
        render_job_card(job)