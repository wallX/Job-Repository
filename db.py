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
                location TEXT,
                workload TEXT,
                contract_type TEXT,
                url TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Detail Page Extraction
                full_description TEXT DEFAULT NULL,
                raw_description_html TEXT DEFAULT NULL,
                
                -- LLM Processing State
                is_junior INTEGER DEFAULT NULL,
                junior_score REAL DEFAULT NULL,
                stack_gap TEXT DEFAULT NULL,
                language_friction TEXT DEFAULT NULL,
                status TEXT DEFAULT 'new'
            )
        """)
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