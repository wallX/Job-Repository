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
                url TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
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
                status TEXT DEFAULT 'new'
            )
        """)
        conn.commit()

def get_unprocessed_jobs(source: str):
    """Fetches jobs from SQLite that haven't had their full description scraped yet."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT job_id, url FROM jobs WHERE full_description IS NULL AND source = ?", (source,))
        return cursor.fetchall()

def update_job_details(job_id: str, pub_date: str = None, workload: str = None, contract: str = None, 
                       location: str = None, salary: str = None, clean_text: str = None, raw_html: str = None):
    """Updates SQLite with newly scraped metadata and full description text."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE jobs 
            SET publication_date = :pub_date,
                workload = :workload,
                contract_type = :contract,
                location = :location,
                salary_estimate = :salary,
                full_description = :clean_text,
                raw_description_html = :raw_html,
                status = 'details_extracted'
            WHERE job_id = :job_id
        """, {
            "pub_date": pub_date,
            "workload": workload,
            "contract": contract,
            "location": location,
            "salary": salary,
            "clean_text": clean_text,
            "raw_html": raw_html,
            "job_id": job_id
        })
        conn.commit()



def insert_job(job_id: str, source: str, title: str, company: str, 
               location: str, workload: str, contract_type: str, url: str):
    """Inserts a new job entry into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO jobs (
                job_id, source, title, company, location, workload, contract_type, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            source,
            title,
            company,
            location,
            workload,
            contract_type,
            url
        ))
        conn.commit()


if __name__ == "__main__":
    init_db()
    print("Database updated.")