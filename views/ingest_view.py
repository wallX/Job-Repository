# views/ingest_view.py
import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import db
from scrapers import get_scraper_for_url


def ingest_urls(urls: list[str] | str, search_terms: list[str] = None):
    """
    Ingests single or multiple URLs and attaches the provided search terms.
    If a job exists, appends new search terms without duplicating them.
    """
    db.init_db()

    # Normalize URLs input
    if isinstance(urls, str):
        raw_list = urls.replace(",", "\n").replace(" ", "\n").splitlines()
        url_list = [u.strip() for u in raw_list if u.strip()]
    else:
        url_list = urls

    search_terms = search_terms or []

    print(f"\n Processing {len(url_list)} URL(s) with search terms: {search_terms}...\n")

    added_count = 0
    updated_count = 0
    log_lines = []

    for idx, raw_url in enumerate(url_list, 1):
        scraper = get_scraper_for_url(raw_url)

        source = scraper.source_name
        job_id = scraper.extract_job_id(raw_url)
        processed_url = scraper.normalize_url(job_id)

        result = db.insert_job(
            job_id=job_id,
            source=source,
            url=processed_url,
            search_terms=search_terms
        )

        prefix = f"[{idx}/{len(url_list)}] {source}/{job_id}"

        if result["is_new"]:
            added_count += 1
            line = f"{prefix} -> Inserted New"
        else:
            updated_count += 1
            line = f"{prefix} -> Appended Terms to Existing"
            if result["archived"]:
                reason = result["reason_for_archival"] or "No reason specified"
                line += f" (Archived - Reason: {reason})"

        print(line)
        log_lines.append(line)

    summary = f"\nFinished: {added_count} new job(s) added, {updated_count} updated with search terms."
    print(summary)

    # Return the detailed logs + summary
    return "\n".join(log_lines) + f"\n\n{summary.strip()}"

def render_ingest_view():
    st.subheader("➕ Ingest New Job Offer")
    st.caption("Enter a job URL and select search terms. The scraper and LLM analyzer will handle the rest.")

    if "available_tags" not in st.session_state:
        st.session_state.available_tags = db.fetch_existing_tags()

    with st.form("manual_ingest_form", clear_on_submit=True):
        url_input = st.text_area(
            "Job Offer URLs",
            placeholder="https://www.jobs.ch/en/vacancies/detail/123...\nhttps://www.jobs.ch/en/vacancies/detail/456...",
            help="Paste one or more job posting links (one per line).",
            height=150
        )

        selected_tags = st.multiselect(
            "Search Terms / Tags",
            options=st.session_state.available_tags,
            default=["Software Engineer"] if "Software Engineer" in st.session_state.available_tags else [],
            accept_new_options=True,
            placeholder="Select or type to add search terms...",
            help="Select existing terms or type a custom term and press Enter."
        )

        submit_button = st.form_submit_button("Queue Job Offer", use_container_width=True)

        if submit_button:
            clean_url = url_input.strip()
            if not clean_url:
                st.error("Please enter a valid Job Offer URL!")
            else:
                try:
                    # 1. Normalize user inputs: trim whitespace and Title Case (e.g., "python dev" -> "Python Dev")
                    normalized_tags = sorted(list({tag.strip().title() for tag in selected_tags if tag.strip()}))

                    # 2. Add new tags to session state while keeping uniqueness
                    for tag in normalized_tags:
                        if tag not in st.session_state.available_tags:
                            st.session_state.available_tags.append(tag)
                    
                    st.session_state.available_tags.sort()

                    # 3. Trigger ingestion with normalized search terms
                    result =ingest_urls(urls=clean_url, search_terms=normalized_tags)

                    # Show a clean top-level success banner
                    st.success("✅ Job offer queued!")

                    # Put the long return string inside a collapsable detail box
                    with st.expander("Show Detailed Log", expanded=True):
                        st.text(result)  # st.text preserves line breaks and spacing cleanly

                except Exception as e:
                    st.error(f"Failed to ingest job offer: {e}")