import sqlite3
from pathlib import Path

DB_PATH = Path("data/pipeline.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT,
                company TEXT,
                company_image_url TEXT DEFAULT NULL,
                url TEXT UNIQUE,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                search_term TEXT DEFAULT NULL,
                
                -- Detail Page Extraction
                publication_date TEXT DEFAULT NULL,
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
                llm_summary TEXT DEFAULT NULL,
                status TEXT DEFAULT 'new',
                applied_at DATETIME DEFAULT NULL
            )
        """)
        conn.commit()

def get_unprocessed_jobs(source: str = "jobs.ch"):
    """Fetches records where full_description is NULL for the target source."""
    if not DB_PATH.exists():
        return []
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_id, url, search_term FROM jobs WHERE full_description IS NULL AND source = ?", 
            (source,)
        )
        return cursor.fetchall()

def update_job_details(
    job_id: str, 
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
                status = 'details_extracted'
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
            "raw_html": raw_html
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


if __name__ == "__main__":
    init_db()
    print("Database updated.")