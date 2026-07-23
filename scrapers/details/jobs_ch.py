import sqlite3
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import sys


# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

DB_PATH = Path("data/pipeline.db")

def safe_extract_text(parent_locator, selector: str) -> str | None:
    """Helper to safely extract text from optional metadata selectors without throwing errors."""
    elem = parent_locator.locator(selector)
    if elem.count() > 0:
        return elem.first.text_content().strip()
    return None

def run_detail_scraper():
    from db import get_unprocessed_jobs, update_job_details
    from scrapers.auth.jobs_ch import get_latest_jwt
    jobs = get_unprocessed_jobs("jobs.ch")
    if not jobs:
        print("No pending job descriptions to scrape.")
        return

    print(f"Found {len(jobs)} jobs pending detail extraction.")

    #jwt_token = get_latest_jwt()


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
        #extra_http_headers={
        #    "Authorization": f"Bearer {jwt_token}"
        #}
    )
        page = context.new_page()

        for idx, job in enumerate(jobs, 1):
            job_id = job["job_id"]
            url = job["url"]

            print(f"[{idx}/{len(jobs)}] Scraping details: {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                info_block = page.locator('div[data-cy="vacancy-info"]')
                info_block.wait_for(timeout=5000)

                # Extract Structured Metadata
                pub_date = safe_extract_text(info_block, 'li[data-cy="info-publication"]')
                workload = safe_extract_text(info_block, 'li[data-cy="info-workload"]')
                contract = safe_extract_text(info_block, 'li[data-cy="info-contract"]')
                #salary = safe_extract_text(info_block, 'li[data-cy="info-salary_estimate"]')

                # Extract Location dynamically (It's the <li> without a dedicated data-cy attribute)
                loc_elem = info_block.locator('li:not([data-cy])')
                location = loc_elem.first.text_content().strip() if loc_elem.count() > 0 else None

                # Extract Main Description Body
                desc_locator = page.locator('div[data-cy="vacancy-description"]')
                clean_text = desc_locator.inner_text().strip()
                raw_html = desc_locator.inner_html().strip()

                # Save directly to SQLite
                update_job_details(job_id, pub_date=pub_date, workload=workload, contract=contract, location=location, clean_text=clean_text, raw_html=raw_html)
                print(f"  Extracted job {job_id} ({len(clean_text)} chars), publication date: {pub_date}, workload: {workload}, contract: {contract}, location: {location}")

            except Exception as e:
                print(f"  Failed to extract details for {job_id}: {e}")

            # Polite anti-bot delay
            time.sleep(1.5)
            #time.sleep(1000000)

    browser.close()


if __name__ == "__main__":
    run_detail_scraper()