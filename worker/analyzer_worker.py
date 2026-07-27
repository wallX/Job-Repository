import sys
from pathlib import Path

from base_worker import BaseWorker

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from analyzer import run_analysis_pipeline  # Your existing pipeline function

class JobAnalyzerWorker(BaseWorker):
    def __init__(self):
        # Service name, 15-second sleep interval, batch size of 10
        super().__init__(service_name="JobAnalyzer", poll_interval=999999, batch_size=1)

    def process_batch(self, batch_size: int) -> int:
        # Executes your pipeline and returns the count of processed items
        items_processed = run_analysis_pipeline(batch_size=batch_size)
        return items_processed

if __name__ == "__main__":
    worker = JobAnalyzerWorker()
    worker.run()