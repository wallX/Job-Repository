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

    for idx, raw_url in enumerate(url_list, 1):
        scraper = get_scraper_for_url(raw_url)

        source = scraper.source_name
        job_id = scraper.extract_job_id(raw_url)

        is_new = db.insert_job(
            job_id=job_id,
            source=source,
            url=raw_url,
            search_terms=search_terms
        )

        if is_new:
            added_count += 1
            print(f"  [{idx}/{len(url_list)}] Inserted New ({source}): {job_id}")
        else:
            updated_count += 1
            print(f"  [{idx}/{len(url_list)}] Appended Terms to Existing: {job_id}")

    print(f"\n Finished: {added_count} new job(s) added, {updated_count} updated with search terms.")

def render_ingest_view():
    st.subheader("Ingest New Job Offer")
    st.caption("Enter a job URL and select search terms. The scraper and LLM analyzer will handle the rest.")

    # Keep track of tag options in session state
    if "available_tags" not in st.session_state:
        st.session_state.available_tags = db.fetch_existing_tags()

    with st.form("manual_ingest_form", clear_on_submit=True):
        # 1. URL Input Field
        url_input = st.text_input(
            "Job Offer URL",
            placeholder="https://www.jobs.ch/en/vacancies/detail/12345678-1234-5678-1234-567812345678/",
            help="Direct web link to the job posting. Supported sources: jobs.ch"
        )

        # 2. Search Terms List Box
        selected_tags = st.multiselect(
            "Search Terms / Tags",
            options=st.session_state.available_tags,
            default=["Python"] if "Python" in st.session_state.available_tags else [],
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
                    # Save any newly typed tags to session state so they persist in the UI
                    for tag in selected_tags:
                        if tag not in st.session_state.available_tags:
                            st.session_state.available_tags.append(tag)

                    # Trigger your exact ingestion logic (extracts job_id & calls insert_job)
                    ingest_urls(urls=clean_url, search_terms=selected_tags)

                    st.success("Job offer queued! The scraper and analyzer will process it automatically.")

                except Exception as e:
                    st.error(f"Failed to ingest job offer: {e}")