from datetime import datetime 
import re
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from patchright.sync_api import sync_playwright
import sys
import time
import random


# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from db import get_unprocessed_jobs, update_job_details
from scrapers.base import BaseScraper
import config

DB_PATH = Path(config.DB_PATH)

class SwissDevJobsScraper(BaseScraper):
    source_name = "swissdevjobs.ch"

    def can_handle_url(self, url: str) -> bool:
        try:
            # Standardize and extract the domain
            netloc = urlparse(url).netloc.lower()

            # Remove port if present (e.g., jobs.ch:8080)
            netloc = netloc.split(":")[0]

            # Match exact domain or subdomains (e.g., www.jobs.ch)
            return netloc == self.source_name or netloc.endswith(f".{self.source_name}")
        except Exception:
            return False

    def run(self, batch_size: int) -> None:
        run_detail_scraper(batch_size=batch_size)


    def extract_job_id(self, url: str) -> str:
        """Extracts the job slug from SwissDevJobs URLs."""
        match = re.search(r'swissdevjobs\.ch/jobs/([\w-]+)', url)
        return match.group(1) if match else str(hash(url))

    def normalize_url(self, job_id: str) -> str:
        """Normalizes the URL for storage in the database.
        This method should return a consistent URL format for the given job_id,
        ensuring that different URL variations for the same job are treated as identical.
        """
        return f"https://www.swissdevjobs.ch/{job_id}/"


import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def parse_relative_date(date_str: str) -> str:
    """
    Parses relative date strings like '3 weeks ago', '2 days ago', '1 month ago'
    and returns a date formatted as YYYY-MM-DD.
    """
    if not date_str:
        return datetime.today().strftime("%Y-%m-%d")

    date_str = date_str.lower().strip()
    
    # Extract the number and the unit (e.g., '3', 'weeks')
    match = re.search(r"(\d+)\s*(day|week|month|year|hour|minute)", date_str)
    if not match:
        # Fallback to current date if format isn't recognized
        return datetime.today().strftime("%Y-%m-%d")

    val, unit = int(match.group(1)), match.group(2)
    today = datetime.now()

    if "day" in unit:
        target_date = today - timedelta(days=val)
    elif "week" in unit:
        target_date = today - timedelta(weeks=val)
    elif "month" in unit:
        target_date = today - relativedelta(months=val)
    elif "year" in unit:
        target_date = today - relativedelta(years=val)
    else: # hours / minutes / seconds default to today
        target_date = today

    return target_date.strftime("%Y-%m-%d")



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


def run_detail_scraper(batch_size: int):
    #from scrapers.old.auth_jobs_ch import get_latest_jwt
    jobs = get_unprocessed_jobs("New", "swissdevjobs.ch", limit=batch_size)
    if not jobs:
        print("No pending 'New' job descriptions to scrape.")
        return

    print(f"Found {len(jobs)} jobs pending detail extraction.")

    #jwt_token = get_latest_jwt()


    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--use-mock-keychain",
                "--no-sandbox",
            ],
            proxy={
                "server": "socks4://69.55.49.177:38182"
               # "username": "my_username",
               # "password": "my_password"
            }
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            #device_scale_factor=1,
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
        )

        page = context.new_page()

        #page.goto('https://whatismyipaddress.com', wait_until="domcontentloaded", timeout=20000);
        #time.sleep(120)
        for idx, job in enumerate(jobs, 1):
            job_id = job["job_id"]
            url = job["url"]

            print(f"[{idx}/{len(jobs)}] Scraping details: {url}")

            try:
                
                page.goto(url, wait_until="domcontentloaded", timeout=15000)

                # 1. Header Information
                title = safe_extract_text(page, 'h1.super-small-header')
                salary = safe_extract_text(page, 'div[aria-label="annual salary range"]')
                company = safe_extract_text(page, 'div[aria-label="hiring organization"]')

                # Extract Company Image URL and clean tracking query parameters
                logo_locator = page.locator('img.job-details-company-image').first

                company_image_url = None

                if logo_locator.count() > 0:
                    logo_locator.wait_for(state="attached", timeout=5000)
                    
                    # Grab full URL
                    raw_url = logo_locator.get_attribute("src")
                    
                    # Ignore base64 placeholders / tracking pixels
                    if raw_url and not raw_url.startswith("data:image"):
                        company_image_url = raw_url

                clean_company_image_url = None
                if company_image_url:
                    parsed = urlparse(company_image_url)
                    clean_company_image_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

                # 2. Structured Metadata
                # SwissDevJobs does not consistently show a publication date in this exact view; fallback added.
                pub_date_raw = safe_extract_text(page, '.publish-date-selector') # Adjust if you have a specific date locator
                sqlite_date = parse_relative_date(pub_date_raw) if pub_date_raw else None

                # Contract, Seniority, Industry rely on specific info cards mapping to their respective icons/badges
                contract = safe_extract_text(
                    page, 
                    'div.job-info-card:has(div.job-essential-info-card-badge:has-text("Job Type")) span.font-weight-bold'
                )
                seniority = safe_extract_text(
                    page, 
                    'div.job-info-card:has(div.job-essential-info-card-badge:has-text("Exp Level")) span.font-weight-bold'
                )
                industry = safe_extract_text(
                    page, 
                    'div.job-info-card:has(div.job-essential-info-card-badge:has-text("Company Type")) span.font-weight-bold'
                )
                function = None # Missing in this specific layout snippet

                # Location
                location = safe_extract_text(page, 'div[aria-label="hiring organization address"]')
                city = extract_city_from_location(location)

                # Swiss jobs heavily feature workloads in the title (e.g., "80-100%"). Extract it via Regex.
                workload = "100%"
                if title:
                    workload_match = re.search(r'(\d{2,3}(?:-\d{2,3})?%)', title)
                    if workload_match:
                        workload = workload_match.group(1)

                # 3. Main Description Body (Raw HTML & Clean Text)
                # SwissDevJobs splits descriptions into multiple boxes (Requirements, Responsibilities, etc.)
                desc_locators = page.locator('div.job-details-section-box')

                if desc_locators.count() > 0:
                    # Join the texts of all description boxes
                    clean_text = "\n\n".join(desc_locators.all_inner_texts()).strip()
                    
                    # Use evaluate_all to fetch outerHTML for all matching elements at once
                    raw_html = desc_locators.evaluate_all(
                        "(elements) => elements.map(el => el.outerHTML).join('\\n')"
                    )
                else:
                    clean_text = None
                    raw_html = None

                # Save directly to SQLite
                update_job_details(
                    job_id,
                    status="Scraped",
                    pub_date=sqlite_date,
                    workload=workload,
                    contract=contract,
                    location=location,
                    salary=salary,  # Note: Pushed extracted salary here
                    clean_text=clean_text,
                    raw_html=raw_html,
                    title=title,
                    company=company,
                    city=city,
                    seniority=seniority,
                    function=function,
                    industry=industry,
                    company_image_url=clean_company_image_url
                )

                print(f"  Extracted job {job_id} ({len(clean_text) if clean_text else 0} chars), workload: {workload}, contract: {contract}, location: {location}, salary: {salary}")

            except Exception as e:
                print(f"  Failed to extract details for {job_id}: {e}")

            # Polite anti-bot delay
            if idx < len(jobs):  # No need to wait after the last job
                jitter = random.uniform(2.3, 5.1)
                print(f"  Waiting {jitter:.2f}s before next request...")
                time.sleep(jitter)
        browser.close()

# Implement as a service

if __name__ == "__main__":
    run_detail_scraper()