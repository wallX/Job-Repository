from base_worker import BaseWorker

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


from run_scrapers import main  # Your existing pipeline function

class DetailScraperWorker(BaseWorker):
    def __init__(self):
        super().__init__(service_name="DetailScraper", poll_interval=30, batch_size=5)

    def process_batch(self, batch_size: int) -> int:
        # Scrapes pending job detail pages from SQLite
        scraped_count = main(batch=batch_size)
        return scraped_count

if __name__ == "__main__":
    worker = DetailScraperWorker()
    worker.run()