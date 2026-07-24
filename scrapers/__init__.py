from scrapers.base import BaseScraper
from scrapers.jobs_ch import JobsChScraper
#from scrapers.linkedin import LinkedInScraper
#from scrapers.swissdevjobs import SwissDevJobsScraper

# Central registry mapping source names to scraper instances
SCRAPER_REGISTRY: dict[str, BaseScraper] = {
    "jobs_ch": JobsChScraper(),
    #"linkedin": LinkedInScraper(),
    #"swissdevjobs": SwissDevJobsScraper(),
}

def get_all_scrapers() -> list[BaseScraper]:
    """Returns a list of all registered scrapers."""
    return list(SCRAPER_REGISTRY.values())

def get_scraper_by_name(name: str) -> BaseScraper | None:
    """Retrieves a specific scraper instance by key name."""
    return SCRAPER_REGISTRY.get(name.lower())

def get_scraper_for_url(url: str) -> BaseScraper:
    """Determines the appropriate scraper for a given URL."""
    for scraper in SCRAPER_REGISTRY.values():
        if scraper.can_handle_url(url):
            return scraper
    raise ValueError(f"No scraper found for URL: {url}")