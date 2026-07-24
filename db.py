import sqlite3
from pathlib import Path
from typing import List

from pydantic import json

DB_PATH = Path("data/pipeline.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                url TEXT UNIQUE,
                search_term TEXT DEFAULT NULL,
                status TEXT DEFAULT 'New',
                
                -- Basic Metadata
                title TEXT,
                company TEXT,
                company_image_url TEXT DEFAULT NULL,

                
                -- Detail Page Extraction
                workload TEXT DEFAULT NULL,
                contract_type TEXT DEFAULT NULL,
                location TEXT DEFAULT NULL,
                city TEXT DEFAULT NULL,
                salary_estimate TEXT DEFAULT NULL,
                full_description TEXT DEFAULT NULL,
                raw_description_html TEXT DEFAULT NULL,
                
                -- LLM Layer Fields
                is_junior INTEGER DEFAULT NULL,
                junior_score REAL DEFAULT NULL,
                stack_gap TEXT DEFAULT NULL,
                language_friction TEXT DEFAULT NULL,
                language_llm TEXT DEFAULT NULL,
                language_llm_only_english INTEGER DEFAULT NULL,
                work_model TEXT DEFAULT NULL,
                required_yoe INTEGER DEFAULT NULL,
                llm_summary TEXT DEFAULT NULL,
                
                -- Timestamps
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                scraped_at DATETIME DEFAULT NULL,
                publication_date DATETIME DEFAULT NULL,
                applied_at DATETIME DEFAULT NULL
            )
        """)
        conn.commit()

def get_unprocessed_jobs(status: str, source: str) -> List[sqlite3.Row]:
    """Fetches records where full_description is NULL for the target source."""
    if not DB_PATH.exists():
        return []
    if status not in ["New", "Scraped", "Processed"]:
        raise ValueError("Invalid status. Must be 'New', 'Scraped', or 'Processed'.")
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_id, url, search_term FROM jobs WHERE full_description IS NULL AND source = ? AND status = ?", 
            (source, status)
        )
        return cursor.fetchall()
########### LLM Evaluation Layer Functions ###########
def get_jobs_pending_llm(limit: int = 20) -> List[sqlite3.Row]:
    """Fetches jobs where details were extracted but LLM analysis hasn't run yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT job_id, title, company, location, full_description 
            FROM jobs 
            WHERE status = 'Scraped' 
              AND full_description IS NOT NULL 
              AND junior_score IS NULL
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def save_llm_evaluation(
    job_id: str,
    is_junior: bool,
    junior_score: float,
    stack_gap: str,
    language_friction: str,
    language_llm: List[str],
    language_llm_only_english: bool,
    work_model: str,
    required_yoe: int,
    llm_summary: str,
    status: str = "Processed"
):
    """Updates SQLite with the structured evaluation result from the LLM."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE jobs 
            SET is_junior = :is_junior,
                junior_score = :junior_score,
                stack_gap = :stack_gap,
                language_friction = :language_friction,
                language_llm = :language_llm,
                llm_summary = :llm_summary,
                language_llm_only_english = :language_llm_only_english,
                work_model = :work_model,
                required_yoe = :required_yoe,
                status = :status
            WHERE job_id = :job_id
        """, {
            "job_id": job_id,
            "is_junior": 1 if is_junior else 0,
            "junior_score": junior_score,
            "stack_gap": stack_gap,
            "language_friction": language_friction,
            "language_llm": language_llm,
            "language_llm_only_english": 1 if language_llm_only_english else 0,
            "llm_summary": llm_summary,
            "work_model": work_model,
            "required_yoe": required_yoe,
            "status": status
        })
        conn.commit()
########### Job Detail Update Functions ###########
def update_job_details(
    job_id: str, 
    status: str,
    pub_date: str = None, 
    workload: str = None, 
    contract: str = None, 
    location: str = None, 
    salary: str = None, 
    clean_text: str = None, 
    raw_html: str = None,
    title: str = None,
    company: str = None,
    city: str = None,
    company_image_url: str = None
):
    """
    Updates SQLite with explicit metadata fields extracted from detail pages.
    COALESCE ensures existing non-null values aren't overwritten by None.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE jobs 
            SET title = COALESCE(:title, title),
                company = COALESCE(:company, company),
                company_image_url = COALESCE(:company_image_url, company_image_url),
                publication_date = COALESCE(:pub_date, publication_date),
                workload = COALESCE(:workload, workload),
                contract_type = COALESCE(:contract, contract_type),
                location = COALESCE(:location, location),
                city = COALESCE(:city, city),
                salary_estimate = COALESCE(:salary, salary_estimate),
                full_description = COALESCE(:clean_text, full_description),
                raw_description_html = COALESCE(:raw_html, raw_description_html),
                status = COALESCE(:status, status),
                scraped_at = CURRENT_TIMESTAMP
            WHERE job_id = :job_id
        """, {
            "job_id": job_id,
            "title": title,
            "company": company,
            "company_image_url": company_image_url,
            "pub_date": pub_date,
            "workload": workload,
            "contract": contract,
            "location": location,
            "city": city,
            "salary": salary,
            "clean_text": clean_text,
            "raw_html": raw_html,
            "status": status
        })
        conn.commit()



def insert_job(job_id: str, source: str, title: str, company: str, 
               location: str, workload: str, contract_type: str, url: str, search_term: str = None):
    """Inserts a new job entry into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO jobs (
                job_id, source, title, company, location, workload, contract_type, url, search_term
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            source,
            title,
            company,
            location,
            workload,
            contract_type,
            url,
            search_term
        ))
        conn.commit()

def insert_job(job_id: str, source: str, url: str, search_terms: list[str] = None) -> bool:
    """
    Inserts a new job entry into the database with minimal fields.
    If the job_id already exists, it appends any new search terms to the existing list.
    """
    search_terms = search_terms or []
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Check if job already exists
        cursor.execute("SELECT search_term FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()

        if row is None:
            # New Entry: Store new search terms as a JSON string
            terms_string = ", ".join(set(search_terms))
            cursor.execute("""
                INSERT INTO jobs (job_id, source, url, search_term, status)
                VALUES (?, ?, ?, ?, 'New')
            """, (job_id, source, url, terms_string))
            conn.commit()
            return True  # Inserted new
        else:
            # Existing Entry: Parse existing JSON array, combine, and update
            existing_raw = row[0]
            existing_terms = []
            
            if existing_raw:
                # Split, trim whitespace, and filter out any empty strings
                existing_terms = [t.strip() for t in existing_raw.split(",") if t.strip()]
                
                # Merge existing and new terms while preserving uniqueness
                combined_terms = existing_terms + search_terms
                unique_terms = list(set(combined_terms))
                
                # Join into a clean, comma-separated string
                updated_json = ", ".join(unique_terms)
            else:
                # Handle case where existing_raw is empty or None
                unique_terms = list(set(search_terms))
                updated_json = ", ".join(unique_terms)

            cursor.execute("""
                UPDATE jobs 
                SET search_term = ? 
                WHERE job_id = ?
            """, (updated_json, job_id))
            conn.commit()
            return False  # Appended to existing



if __name__ == "__main__":
    init_db()
    print("Database updated.")