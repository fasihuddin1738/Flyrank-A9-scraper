# The Polite Scraper

A resilient, polite data extraction pipeline built in Python. This scraper downloads catalogue pages from a practice sandbox, extracts product details, validates them against a strict schema, and safely handles broken pages without crashing.

## 🎯 Target Classification
* **Target Site:** Books to Scrape (https://books.toscrape.com/)
* **Reason:** It is a public practice sandbox explicitly built for people to learn scraping[cite: 1].
* **Scope:** Only the first 3 catalogue pages and their associated book detail pages[cite: 1].
* **Data Collected:** Book title, product URL, price, availability, rating, and description[cite: 1].
* **Robots.txt Check:** No robots file found (returned 404 Not Found)[cite: 1].

I will not reuse this code on another site without checking its rules and terms first[cite: 1].

## 🛠️ Installation & Lane
This project was built in the **Python lane**[cite: 1].

1. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate

    ```

2. Install dependencies:
    ```bash
    pip install requests beautifulsoup4 pydantic

    ```



## ▶️ Usage

Run the pipeline with a single command:

```bash
python main.py

```

## 🤝 Politeness Rules Followed

This scraper acts as a responsible guest on the host server:

* **Identification:** Sends an honest `User-Agent` header containing contact/repo information.


* **Pacing:** Enforces a minimum 0.5-second delay between all live requests.


* **Timeouts:** All requests have a strict 10-second timeout to prevent hanging.


* **Caching:** Development runs read from local cache; live servers are only hit once per page.



## 🗄️ Record Schema

Data is validated using Pydantic before storage:

* `title` (string)
* `product_url` (string, canonical identity)
* `price_text` (string)
* `price_gbp` (float, normalized)
* `availability_text` (string)
* `rating_text` (string, optional)
* `description` (string, optional)
* `source_page` (string, provenance)
* `fetched_at` (ISO 8601 timestamp)

## ⚖️ Ethics & Architecture Notes

* **Ethics:** Always use an official API when one exists. Never bypass logins, paywalls, or blocks, and strictly collect only the data you need.


* **Architecture:** This assignment needed no browser (like Playwright or Selenium) because the required data is already present in the raw HTML the server sends; rendering a full browser would only add unnecessary memory and processing cost.


* **Limitation:** The script currently relies on hardcoded CSS selectors; if the target site changes its HTML structure or class names, the extraction logic will break and require maintenance.

## 📊 Sample Run Report

```json
{
  "start_time": "2026-08-13T23:13:39Z",
  "duration_seconds": 3.18,
  "pages_fetched": 1,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 1,
  "failed_pages": 1
}

```

*(Note: 1 failed page is deliberately injected to test error handling)*