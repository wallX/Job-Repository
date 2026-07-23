import json
from pathlib import Path
from playwright.sync_api import sync_playwright

RAW_DATA_PATH = Path("data/raw_api_jobs.jsonl")


def get_latest_jwt(jsonl_path="data/raw_api_jobs.jsonl") -> str:
    """Finds the most recently intercepted JWT token from raw logs."""
    jwt = None
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if "issue-token" in data.get("url", ""):
                payload = data.get("payload", {})
                if "jwt" in payload:
                    jwt = payload["jwt"]
    return jwt


def handle_response(response):
    # Intercept network calls to job listing or detail endpoints
    # Adjust URL pattern based on what you saw in Safari DevTools Network Tab
    if "api" in response.url and response.status == 200:
        try:
            # Inspect content-type to ensure it's JSON
            if "application/json" in response.headers.get("content-type", ""):
                data = response.json()
                print(f"⚡ Intercepted API Payload from: {response.url}")
                
                # Save raw payload immediately (ELT zero-loss principles)
                with open(RAW_DATA_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"url": response.url, "payload": data}) + "\n")
        except Exception as e:
            pass

def run_intercept_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Attach response listener BEFORE navigating
        page.on("response", handle_response)

        print("Navigating to jobs.ch...")
        page.goto("https://www.jobs.ch/en/jobs/?term=python")
        page.wait_for_timeout(1000000) # Give API time to fire

        browser.close()

if __name__ == "__main__":
    run_intercept_scraper()