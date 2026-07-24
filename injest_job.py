import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db import init_db, insert_job
from scrapers import get_scraper_for_url

def ingest_urls(urls: list[str] | str, search_terms: list[str] = None):
    """
    Ingests single or multiple URLs and attaches the provided search terms.
    If a job exists, appends new search terms without duplicating them.
    """
    init_db()

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

        is_new = insert_job(
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

if __name__ == "__main__":
    init_db()
    
    # Example usage:
    links_to_add = [
        "https://www.jobs.ch/en/vacancies/detail/cc950237-d3a0-4eaa-aa97-7dc7441bb6ca/",
    ]
    terms = ["Developer"]

    ingest_urls(links_to_add, search_terms=terms)