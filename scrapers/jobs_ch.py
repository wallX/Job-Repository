import re
import sqlite3
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from db import get_unprocessed_jobs, update_job_details
import sys
import time
import random
from scrapers.base import BaseScraper
import config

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

DB_PATH = Path(config.DB_PATH)

class JobsChScraper(BaseScraper):
    source_name = "jobs_ch"

    def can_handle_url(self, url: str) -> bool:
        return "jobs.ch" in url

    def run(self) -> None:
        JobsChScraperService()

    def extract_job_id(self, url: str) -> str:
        """Extracts GUID from vacancy URLs like /en/vacancies/detail/24d79bae-.../"""
        match = re.search(r'/detail/([a-f0-9\-]+)/?', url)
        return match.group(1) if match else str(hash(url))





def safe_extract_text(parent_locator, selector: str) -> str | None:
    elem = parent_locator.locator(selector)
    if elem.count() > 0:
        return elem.first.text_content().strip()
    return None

def safe_extract_attribute(parent_locator, selector: str, attribute: str) -> str | None:
    """Safely extracts an attribute (e.g. 'src') from a selector."""
    elem = parent_locator.locator(selector)
    if elem.count() > 0:
        val = elem.first.get_attribute(attribute)
        return val.strip() if val else None
    return None

def extract_city_from_location(location_str: str | None) -> str | None:
    if not location_str:
        return None
    primary = location_str.split('/')[0].split(',')[0].strip()
    words = [w for w in primary.split() if not w.isdigit()]
    return " ".join(words) if words else primary

def filter_jobs_by_terms(jobs: list, search_terms: list[str] | str) -> list:
    if search_terms == "all" or not search_terms:
        return jobs

    target_terms = [t.lower().strip() for t in search_terms] if isinstance(search_terms, list) else [search_terms.lower().strip()]
    
    filtered = []
    for job in jobs:
        job_terms = job["search_term"].lower() if job["search_term"] else ""
        if any(term in job_terms for term in target_terms):
            filtered.append(job)
            
    return filtered


def run_detail_scraper():
    #from scrapers.old.auth_jobs_ch import get_latest_jwt
    jobs = get_unprocessed_jobs("jobs.ch")
    if not jobs:
        print("No pending job descriptions to scrape.")
        return

    print(f"Found {len(jobs)} jobs pending detail extraction.")

    #jwt_token = get_latest_jwt()


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for idx, job in enumerate(jobs, 1):
            job_id = job["job_id"]
            url = job["url"]

            print(f"[{idx}/{len(jobs)}] Scraping details: {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
                # 1. Header Information
                title = safe_extract_text(page, 'h2[data-cy="vacancy-title"]')
                company = safe_extract_text(page, 'a[data-cy="company-link"]')
                logo_block = page.locator('div[data-cy="vacancy-logo"]')
                company_image_url = safe_extract_attribute(logo_block, 'img', 'src')

                # 2. Structured Metadata
                info_block = page.locator('div[data-cy="vacancy-info"]')
                info_block.wait_for(timeout=5000)
                
                pub_date = safe_extract_text(info_block, 'li[data-cy="info-publication"]')
                workload = safe_extract_text(info_block, 'li[data-cy="info-workload"]')
                contract = safe_extract_text(info_block, 'li[data-cy="info-contract"]')
                #salary = safe_extract_text(info_block, 'li[data-cy="info-salary_estimate"]')

                # Extract Location dynamically (It's the <li> without a dedicated data-cy attribute)
                loc_elem = info_block.locator('li:not([data-cy])')
                location = loc_elem.first.text_content().strip() if loc_elem.count() > 0 else None

                city = extract_city_from_location(location)

                # Extract Main Description Body
                desc_locator = page.locator('div[data-cy="vacancy-description"]')
                clean_text = desc_locator.inner_text().strip()
                raw_html = desc_locator.inner_html().strip()

                # Save directly to SQLite
                # Pass straight to database module
                update_job_details(
                    job_id,
                    pub_date=pub_date,
                    workload=workload,
                    contract=contract,
                    location=location,
                    salary=None,
                    clean_text=clean_text,
                    raw_html=raw_html,
                    title=title,
                    company=company,
                    city=city,
                    company_image_url=company_image_url
                )
                print(f"  Extracted job {job_id} ({len(clean_text)} chars), publication date: {pub_date}, workload: {workload}, contract: {contract}, location: {location}")

            except Exception as e:
                print(f"  Failed to extract details for {job_id}: {e}")

            # Polite anti-bot delay
            jitter = random.uniform(2.3, 5.1)
            print(f"  Waiting {jitter:.2f}s before next request...")
            time.sleep(jitter)
            #time.sleep(1000000)

    browser.close()

# Implement as a service
def JobsChScraperService():
    run_detail_scraper()

if __name__ == "__main__":
    JobsChScraperService()