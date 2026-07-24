import argparse
import sys
import time
from scrapers import SCRAPER_REGISTRY, get_all_scrapers, get_scraper_by_name
from db import init_db

def run_pipeline(batch_size: int = 10, target_sources: list[str] = None):
    # Ensure database schema exists before scraping
    init_db()

    # Determine which scrapers to execute
    if not target_sources or "all" in target_sources:
        scrapers_to_run = get_all_scrapers()
    else:
        scrapers_to_run = []
        for name in target_sources:
            scraper = get_scraper_by_name(name)
            if scraper:
                scrapers_to_run.append(scraper)
            else:
                print(f" Warning: Scraper '{name}' not found. Available: {list(SCRAPER_REGISTRY.keys())}")

    if not scrapers_to_run:
        print(" No valid scrapers selected. Exiting.")
        return

    print(f" Starting Scraper Pipeline with {len(scrapers_to_run)} target(s)...")

    for idx, scraper in enumerate(scrapers_to_run, 1):
        print(f"==================================================")
        print(f"[{idx}/{len(scrapers_to_run)}] Running Scraper: {scraper.source_name}")
        print(f"==================================================")
        
        start_time = time.time()
        try:
            scraper.run(batch_size=batch_size)
            duration = time.time() - start_time
            print(f" Completed '{scraper.source_name}' in {duration:.1f}s\n")
        except Exception as e:
            print(f" Error during '{scraper.source_name}' execution: {e}\n")

    print(" All scrapers finished.")

def main(batch: int = 10):
    parser = argparse.ArgumentParser(description="Central Scraper Pipeline CLI")
    parser.add_argument(
        "--source", "-s",
        nargs="+",
        default=["all"],
        help=f"Specific scraper(s) to run (choices: {list(SCRAPER_REGISTRY.keys())} or 'all'). Default: 'all'"
    )
    parser.add_argument(
        "--batch", "-b",
        type=int,
        default=10,
        help="Batch size for processing. Default: 10"
    )

    args = parser.parse_args()

    run_pipeline(batch_size=args.batch, target_sources=args.source)

if __name__ == "__main__":
    main()