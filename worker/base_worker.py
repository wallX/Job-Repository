import abc
import logging
import signal
import sys
import time

# Ensure logs output instantly in Docker containers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


class BaseWorker(abc.ABC):
    """Abstract Base Class for continuous background service workers."""

    def __init__(self, service_name: str, poll_interval: int = 15, batch_size: int = 10):
        self.service_name = service_name
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.running = True
        self.logger = logging.getLogger(self.service_name)

        # Register termination signals for graceful Docker shutdowns
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        self.logger.info("Shutdown signal received. Completing active work before exit...")
        self.running = False

    @abc.abstractmethod
    def process_batch(self, batch_size: int) -> int:
        """Execute one cycle of work.

        Must return the integer count of items processed.
        Subclasses must implement this method.
        """
        pass

    def run(self):
        """Starts the infinite polling loop."""
        self.logger.info(
            f"Service started (poll_interval={self.poll_interval}s, batch_size={self.batch_size})"
        )

        while self.running:
            try:
                processed_count = self.process_batch(self.batch_size) or 0

                # Adaptive Polling: If batch was full, skip sleeping to clear the queue
                if processed_count >= self.batch_size:
                    self.logger.info(
                        f"Processed {processed_count} items (full batch). Continuing immediately..."
                    )
                    continue

            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}", exc_info=True)

            # Sleep in 1-second increments to allow instant response to shutdown signals
            for _ in range(self.poll_interval):
                if not self.running:
                    break
                time.sleep(1)

        self.logger.info("Service stopped cleanly.")