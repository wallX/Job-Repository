import sqlite3
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DB_PATH = Path("data/pipeline.db")

def get_unprocessed_jobs():
    """Fetches jobs from SQLite that haven't had their full description scraped yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT job_id, url FROM jobs WHERE full_description IS NULL")
        return cursor.fetchall()


def update_job_description(job_id: str, clean_text: str, raw_html: str):
    """Updates the job entry with full detail content."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE jobs 
            SET full_description = ?, 
                raw_description_html = ?,
                status = 'details_extracted'
            WHERE job_id = ?
        """, (clean_text, raw_html, job_id))
        conn.commit()

def run_detail_scraper():
    jobs = get_unprocessed_jobs()
    if not jobs:
        print("No pending job descriptions to scrape.")
        return

    print(f"Found {len(jobs)} jobs pending detail extraction.")




if __name__ == "__main__":
    run_detail_scraper()