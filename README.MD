# Job Scraper

Job Scraper is a local job-aggregation and analysis app built around Streamlit, SQLite, Playwright-based scraping, and LLM-driven job evaluation. It collects job postings from supported sources, stores them in a local database, enriches the records with extracted metadata, and uses a CV-aware analysis pipeline to score fit, summarize roles, and support manual tracking.



## Project Summary

This is a useful prototype that already covers the full job-search loop: capture, scrape, analyze, and review. It was intentionally built as a fast, casual and fun experiment rather than a scalable product, so some rough edges are expected. The biggest strengths are the clear workflow from job ingest until job offer evaluation and a dashboard that allows me to keep track of whether a job is worth applying to, whether I already applied, and how the application is progressing over time. The biggest weaknesses are the absence of tests, duplicated logic, hardcoded runtime assumptions, and inconsistent code quality. Security hardening is intentionally a low priority here because this tool is meant to run locally, not as a public web service. If the goal is to evolve this into a reliable tool, the next priority should be cleanup, code scalability and reproducibility before adding more features.

## Proposal

The project is aiming to become a personal job intelligence hub rather than a simple scraper. It was built in a very casual, exploratory way for fun, without worrying too much about scalable system design or a perfectly clean architecture. The code was assembled in about 3 days, with an LLM used to help with small partial code blocks instead of generating the full project in one shot. The intended workflow is:

1. Collect job URLs from supported sources or paste them manually into the app.
2. Normalize and store the job record in SQLite.
3. Scrape the detail page to extract structured metadata and the full description.
4. Run an LLM pass to classify the role, estimate fit against the CV, and generate tags and summaries.
5. Review jobs in the Streamlit dashboard, track application status, archive irrelevant offers, and keep conversation history per job.

The strongest version of this project is a small local product with three clear layers:

1. Ingestion and scraping.
2. Persistent storage and enrichment.
3. Human review and decision support.

The project also behaves like 3 services working together:

1. The UI service, which lets the user add job links, browse the dashboard, and review application status.
2. The scraper service, which takes new job links, fetches the detail page, extracts metadata, and moves the record into `Scraped` state.
3. The analyzer service, which reads the scraped job data, compares it against the candidate information, and produces the LLM evaluation.

In practice, the usage flow is simple:

1. The user adds a job offer link as a `New` entry.
2. The scraper service fetches the available details from the page and stores the job as `Scraped`.
3. The analyzer service evaluates the job against the candidate profile using the CV PDF and the prompt context from `data/user.md` and the other project prompt files.

## What Is Already Done

### Core features

- A Streamlit UI exists in [app.py](/Users/alex/Developer/Job%20Scraper/app.py) with navigation between the job list and manual ingestion.
- Manual ingestion is implemented in [views/ingest_view.py](/Users/alex/Developer/Job%20Scraper/views/ingest_view.py) and also exposed through the CLI-style helper in [injest_job.py](/Users/alex/Developer/Job%20Scraper/injest_job.py).
- A scraper registry exists in [scrapers/__init__.py](/Users/alex/Developer/Job%20Scraper/scrapers/__init__.py) and currently supports jobs.ch, LinkedIn, and SwissDevJobs.
- Detail extraction is implemented for those sources in [scrapers/jobs_ch.py](/Users/alex/Developer/Job%20Scraper/scrapers/jobs_ch.py), [scrapers/linkedin_com.py](/Users/alex/Developer/Job%20Scraper/scrapers/linkedin_com.py), and [scrapers/swissdevjobs_ch.py](/Users/alex/Developer/Job%20Scraper/scrapers/swissdevjobs_ch.py).
- The persistence layer in [db.py](/Users/alex/Developer/Job%20Scraper/db.py) creates and updates a local SQLite database, stores chat history, supports application tracking, and archives jobs.
- LLM analysis is implemented in [analyzer.py](/Users/alex/Developer/Job%20Scraper/analyzer.py) using LiteLLM, Instructor, Pydantic schemas, and prompt files from the data folder.
- The dashboard includes job filtering, job detail dialogs, application status updates, archival, and per-job chat behavior in [views/list_view.py](/Users/alex/Developer/Job%20Scraper/views/list_view.py).
- The project already defines environment-driven configuration in [config.py](/Users/alex/Developer/Job%20Scraper/config.py), including model names, API base URL, prompt paths, and CV path.

### Data and model layer

- The database schema stores raw metadata, extracted description text, LLM scores, candidate fit, language friction, archive status, application status, notes, and timestamps.
- Separate Pydantic models exist under [BaseModels/](/Users/alex/Developer/Job%20Scraper/BaseModels) for role classification, language and inclusivity, candidate evaluation, and job evaluation.
- The app already preserves both operational data and user-facing review data, which is useful for long-term job search tracking.

## What Is Missing

### Product gaps

- Source-specific scraping coverage is still limited to three sources.
- There is no visible task automation for formatting, linting, or verification.

### Code-level gaps

- [db.py](/Users/alex/Developer/Job%20Scraper/db.py) defines insert_job twice, which is a maintainability risk and makes the effective behavior easy to misunderstand.
- The scraper base classes still contain placeholder methods with pass, which means the contract is only partially enforced by implementation.
- The scraping layer has repeated helper logic across source implementations, especially for extraction and normalization.
- Hardcoded proxy settings appear in the scraper implementations, which makes the app brittle outside the current environment.
- Several modules use print for operational output instead of structured logging.
- The repository has inconsistent naming, including injest_job.py, which appears to be a typo.

## Good Practices

- The project uses a clear pipeline: ingest, scrape, enrich, analyze, review.
- Database initialization is centralized, which helps keep the schema consistent.
- The scraper registry is explicit, so adding a new source has a single registration point.
- The code separates UI, scraping, database, and analysis concerns into different modules.
- Configuration is not fully hardcoded; prompt paths, API base URL, model names, and CV path can be driven by environment variables.
- The app stores both structured metrics and human-readable notes, which makes the tool useful for iterative job search workflows.
- Soft archival is used instead of hard deletion, which preserves history.

## Bad Practices

- The code base currently mixes prototype behavior with production-style persistence, which raises maintenance risk.
- Some HTML rendering in the Streamlit UI uses unsafe_allow_html, which should be treated carefully because it can become a security and maintainability issue.
- Several modules depend on broad try/except patterns and console printing rather than structured error handling.
- The repository lacks tests, so regressions in scraping, parsing, or database updates would be hard to catch.
- The naming and spelling quality is uneven, which lowers trust in the codebase and makes it harder to navigate.

## Checklist

### Completed

- [x] Streamlit dashboard exists.
- [x] Manual URL ingestion exists.
- [x] SQLite persistence exists.
- [x] Multiple scraper sources are registered.
- [x] Detail extraction is implemented for each supported source.
- [x] LLM-based analysis pipeline exists.
- [x] Application tracking and archival are supported.
- [x] Job chat history is stored per job.
### To Do

- [ ] Add automated tests for ingestion, scraping, and database updates.

- [ ] Remove duplicate function definitions and consolidate shared database logic.
- [ ] Replace hardcoded runtime values such as proxy settings with configuration.
- [ ] Add a proper logging strategy.
- [ ] Normalize naming and fix obvious typos in filenames.
- [ ] Document the supported environment variables and required local assets.
- [ ] Add a setup and run guide for first-time users.
- [ ] Add dependency pinning or a reproducible dependency lock strategy.
- [ ] Review HTML rendering for safety and long-term maintainability.
- [ ] Improve the BaseModels to better match the real evaluation outputs.
- [ ] Better tune the LLM evaluation base prompt so the scoring and reasons are more accurate.
- [ ] Add pagination to the job listing view.

## Suggested Run Flow
This is a personal job-offer repository and tracking tool. If you want to experiment with it, you need Python and an Ollama-like API endpoint.
1. Install the dependencies from requirements.txt.
2. Create the expected local environment variables.
3. Ensure the CV file exists at the configured path.
4. Create the database by running [db.py](/Users/alex/Developer/Job%20Scraper/db.py).
5. Start the Streamlit app.
6. Ingest a job URL so it enters the database as `New`.
7. Run the scraper service so the job moves to `Scraped` after extracting page details.
8. Run the analyzer service so the LLM compares the job against the candidate profile using the CV PDF and the prompt files.
9. Review the extracted metadata and LLM results in the dashboard.


