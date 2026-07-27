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

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone


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
        return f"https://www.swissdevjobs.ch/jobs/{job_id}/"





def clean_html_text(raw_html):
    """Strips HTML tags, list bullets, and standardizes spacing."""
    if not isinstance(raw_html, str):
        return raw_html
    # Remove HTML tags
    text = BeautifulSoup(raw_html, "html.parser").get_text(separator="\n")
    # Clean leading bullets and excess whitespace
    lines = [re.sub(r'^\s*[\bullet•\-\*]\s*', '', line).strip() for line in text.splitlines()]
    # Filter empty lines
    return "\n".join([line for line in lines if line])

def parse_and_clean_job_posting(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: Status {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Locate all application/ld+json scripts
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    
    job_data = None
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if data.get("@type") == "JobPosting":
                job_data = data
                break
        except (json.JSONDecodeError, TypeError):
            continue

    if not job_data:
        print("No JobPosting Schema found.")
        return None

    # Clean long-text fields
    cleaned_job = {
        "title": job_data.get("title"),
        "company": job_data.get("hiringOrganization", {}).get("name"),
        "company_website": job_data.get("hiringOrganization", {}).get("sameAs"),
        "logo_url": job_data.get("hiringOrganization", {}).get("logo"),
        "date_posted": job_data.get("datePosted"),
        "valid_through": job_data.get("validThrough"),
        "employment_type": job_data.get("employmentType"),
        "salary": {
            "currency": job_data.get("baseSalary", {}).get("currency"),
            "min": job_data.get("baseSalary", {}).get("value", {}).get("minValue"),
            "max": job_data.get("baseSalary", {}).get("value", {}).get("maxValue"),
            "unit": job_data.get("baseSalary", {}).get("value", {}).get("unitText"),
        },
        "location": {
            "locality": job_data.get("jobLocation", {}).get("address", {}).get("addressLocality"),
            "region": job_data.get("jobLocation", {}).get("address", {}).get("addressRegion"),
            "street": job_data.get("jobLocation", {}).get("address", {}).get("streetAddress"),
            "postal_code": job_data.get("jobLocation", {}).get("address", {}).get("postalCode"),
            "country": job_data.get("jobLocation", {}).get("address", {}).get("addressCountry", {}).get("name"),
        },
        "skills_required": clean_html_text(job_data.get("skills")),
        "responsibilities": clean_html_text(job_data.get("responsibilities")),
        "qualifications_tech_stack": job_data.get("qualifications"),
        "benefits": job_data.get("jobBenefits"),
        "description": clean_html_text(job_data.get("description")),
        "same_as_url": job_data.get("sameAs")
    }

    return cleaned_job


# Helper to clean duplicate line breaks, whitespace, and strip HTML
def sanitize_text(value):
    if not value:
        return ""
    # Apply your HTML cleaning logic
    text = clean_html_text(value) if callable(clean_html_text) else str(value)
    # Normalize multiple newlines/spaces
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

# Helper to format multiline text or lists into clean bullet points
def format_bullets(value):
    text = sanitize_text(value)
    if not text:
        return ""
    
    # If passed as a list (e.g. benefits/qualifications)
    if isinstance(value, list):
        return "\n".join(f"• {str(item).strip()}" for item in value if str(item).strip())
        
    # If comma-separated single line (like benefits/tech stack)
    if "," in text and "\n" not in text:
        items = [item.strip() for item in text.split(",") if item.strip()]
        return "\n".join(f"• {item}" for item in items)

    # If multiline text
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(f"• {line.lstrip('•-*\t ')}" for line in lines)


def run_detail_scraper(batch_size: int):
    #from scrapers.old.auth_jobs_ch import get_latest_jwt
    jobs = get_unprocessed_jobs("New", "swissdevjobs.ch", limit=batch_size)
    if not jobs:
        print("No pending 'New' job descriptions to scrape.")
        return

    print(f"Found {len(jobs)} jobs pending detail extraction.")

    #jwt_token = get_latest_jwt()


    with sync_playwright() as p:


        for idx, job in enumerate(jobs, 1):
            job_id = job["job_id"]
            url = job["url"]

            print(f"[{idx}/{len(jobs)}] Scraping details: {url}")

            try:
                cleaned_data = parse_and_clean_job_posting(url)
                dt = datetime.fromisoformat(cleaned_data["date_posted"].replace("Z", "+00:00"))
                loc_data = cleaned_data.get("location", {})
                location_parts = [
                    loc_data.get("street"),
                    loc_data.get("locality"),
                    loc_data.get("region"),
                    loc_data.get("postal_code"),
                    loc_data.get("country"),
                ]
                # Filters out None/empty values and joins them with commas
                formatted_location = ", ".join(filter(None, location_parts))
                #print(f"  Extracted job {job_id}, {formatted_location}")
                #print(json.dumps(cleaned_data, indent=2, ensure_ascii=False))

                skills = format_bullets(cleaned_data.get("skills_required"))
                responsibilities = format_bullets(cleaned_data.get("responsibilities"))
                qualifications = sanitize_text(cleaned_data.get("qualifications_tech_stack"))
                benefits = format_bullets(cleaned_data.get("benefits"))
                raw_desc = sanitize_text(cleaned_data.get("description"))


                merged_description_sections = []

                #if raw_desc:
                    #merged_description_sections.append(f"=== OVERVIEW ===\n{raw_desc}")
                if responsibilities:
                    merged_description_sections.append(f"=== RESPONSIBILITIES ===\n{responsibilities}")
                if skills:
                    merged_description_sections.append(f"=== REQUIREMENTS & SKILLS ===\n{skills}")
                if qualifications:
                    merged_description_sections.append(f"=== TECH STACK ===\n{qualifications}")
                if benefits:
                    merged_description_sections.append(f"=== BENEFITS ===\n{benefits}")

                # Combine all non-empty sections with spacing
                consolidated_description = "\n\n".join(merged_description_sections)

                #print(consolidated_description)


                # Save directly to SQLite
                update_job_details(
                    job_id,
                    status="Scraped",
                    pub_date=dt.strftime("%Y-%m-%d %H:%M:%S"),
                    #workload=workload,
                    contract=cleaned_data["employment_type"],
                    location=formatted_location,
                    salary=f"{cleaned_data['salary']['min']}-{cleaned_data['salary']['max']} {cleaned_data['salary']['currency']}",
                    clean_text=consolidated_description,
                    #raw_html=raw_html,
                    title=cleaned_data.get("title"),
                    company=cleaned_data.get("company"),
                    city=loc_data.get("locality"),
                    #seniority=cleaned_data.get("seniority"),
                    #function=cleaned_data.get("function"),
                    #industry=cleaned_data.get("industry"),
                    company_image_url=cleaned_data.get("logo_url"),
                )

                print(f"  Extracted job {job_id} ({len(consolidated_description or '')} chars), publication date: {dt.strftime("%Y-%m-%d %H:%M:%S")}, location: {loc_data.get("locality")}")


            except Exception as e:
                print(f"  Failed to extract details for {job_id}: {e}")

            # Polite anti-bot delay
            if idx < len(jobs):  # No need to wait after the last job
                jitter = random.uniform(2.3, 5.1)
                print(f"  Waiting {jitter:.2f}s before next request...")
                time.sleep(jitter)

# Implement as a service

if __name__ == "__main__":
    run_detail_scraper(batch_size=10)  # Default batch size for standalone execution