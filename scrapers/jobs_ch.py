import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

RAW_DATA_PATH = Path("data/raw_jobs.jsonl")

def save_raw_payload(payload: dict):
    """Appends payload to local JSONL staging file."""
    RAW_DATA_PATH.parent.mkdir(exist_ok=True)
    with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def extract_job_id(url: str) -> str:
    """Extracts GUID from vacancy URLs like /en/vacancies/detail/24d79bae-.../"""
    match = re.search(r'/detail/([a-f0-9\-]+)/?', url)
    return match.group(1) if match else str(hash(url))

def save_db_payload(payload: dict):
    """Inserts payload into SQLite database."""
    from db import insert_job  # Import here to avoid circular dependency
    insert_job(
        job_id=payload["job_id"],
        source=payload["source"],
        title=payload["title"],
        company=payload["company"],
        location=payload.get("location", ""),
        workload=payload.get("workload", ""),
        contract_type=payload.get("contract_type", ""),
        url=payload["url"]
    )

def run_scraper(search_term="python", max_pages=3):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for background execution
        context = browser.new_context()
        page = context.new_page()

        url = f"https://www.jobs.ch/en/jobs/?sort-by=date&term={search_term}"
        print(f"Navigating to: {url}")
        page.goto(url)

        current_page = 1

        while current_page <= max_pages:
            print(f"\n--- Scraping Page {current_page} ---")
            
            # Wait until the job list renders
            page.wait_for_selector('div[aria-label="Job list"]')
            
            # Select ONLY valid job items (ignores survey/ad cards)
            items = page.locator('div[data-cy="serp-item"]').all()
            print(f"Found {len(items)} jobs on this page.")

            for item in items:
                link_elem = item.locator('a[data-cy="job-link"]').first
                href = link_elem.get_attribute("href") or ""
                title = link_elem.get_attribute("title") or ""
                
                # Extract paragraph metadata (Place of work, Workload, Contract type)
                paragraphs = item.locator("p.textStyle_caption1").all_text_contents()
                clean_paragraphs = [
                                    p.strip() for p in paragraphs 
                                    if p.strip() and "Is this job relevant to you?" not in p
                                ]
                
                # The company name sits in a bold paragraph at the bottom of the card
                company = item.locator("p.fw_bold").text_content() or "Unknown"

                job_url = f"https://www.jobs.ch{href}" if href.startswith("/") else href
                job_id = extract_job_id(href)

                raw_payload = {
                    "job_id": job_id,
                    "source": "jobs.ch",
                    "title": title.strip(),
                    "company": company.strip(),
                    "url": job_url,
                    "raw_meta_paragraphs": clean_paragraphs,
                   #"raw_html": item.inner_html()
                }

                save_raw_payload(raw_payload)
                save_db_payload(raw_payload)
                print(f"  Saved: {title.strip()} @ {company.strip()}")

            # Pagination handling
            next_button = page.locator('a[data-cy="paginator-next"]')
            if next_button.count() > 0 and current_page < max_pages:
                current_page += 1
                next_button.click()
                page.wait_for_timeout(2000)  # Brief wait for AJAX list refresh
            else:
                print("\nReached the end of available pages.")
                break

        browser.close()

if __name__ == "__main__":
    run_scraper(search_term="python", max_pages=2)