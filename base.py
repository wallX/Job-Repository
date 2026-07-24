from abc import ABC, abstractmethod
import re

class BaseScraper(ABC):
    @abstractmethod
    def extract_job_id(self, url: str) -> str:
        """Extracts unique ID/GUID from the URL."""
        pass

    @abstractmethod
    def fetch_details(self, url: str) -> tuple[str, str]:
        """Opens URL in Playwright and returns (clean_text, raw_html)."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Returns the canonical source identifier (e.g. 'jobs.ch', 'linkedin')."""
        pass

    def generic_hash_id(self, url: str) -> str:
        """Fallback ID generator if no regex ID pattern matches."""
        match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', url)
        if match:
            return match.group(1)
        # Try extracting numeric IDs common in URLs (e.g., LinkedIn job IDs)
        numeric_match = re.search(r'/(\d{8,})', url)
        return numeric_match.group(1) if numeric_match else str(hash(url))