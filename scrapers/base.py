from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name identifier for the source (e.g. 'jobs_ch')."""
        pass

    @abstractmethod
    def run(self) -> None:
        """Primary execution method for running the scraper."""
        pass

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Determines if this scraper can handle the given URL."""
        pass

    @abstractmethod
    def extract_job_id(self, url: str) -> str:
        """Extracts a unique job identifier from the given URL."""
        pass