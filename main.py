#USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"
import os
import time
import requests
import json
import re
from urllib.parse import urljoin
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ValidationError

# Constants
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"

# Tracking metrics for our final report
stats = {
    "pages_fetched": 0,
    "cache_hits": 0,
    "valid_records": 0,
    "invalid_records": 0,
    "failed_pages": 0
}

class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str | None = None
    description: str | None = None
    source_page: str
    fetched_at: str

def get_soup_politely(url, cache_filename):
    """Fetches a page, uses cache, handles timeouts/5xx with retries, ignores 40x."""
    os.makedirs("cache", exist_ok=True)
    cache_file = os.path.join("cache", cache_filename)
    
    if os.path.exists(cache_file):
        stats["cache_hits"] += 1
        with open(cache_file, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")
            
    # Retry logic for real requests
    max_attempts = 2
    for attempt in range(max_attempts):
        time.sleep(0.5) 
        stats["pages_fetched"] += 1
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
            
            # Do not retry 404 or 403
            if response.status_code in [403, 404]:
                print(f"Skipping {url}: Status {response.status_code}")
                stats["failed_pages"] += 1
                return None
                
            # Retry on server error (5xx)
            if response.status_code >= 500:
                if attempt < max_attempts - 1:
                    print(f"Server error {response.status_code}. Retrying...")
                    time.sleep(2)
                    continue
                else:
                    stats["failed_pages"] += 1
                    return None
                    
            if response.status_code == 200:
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                return BeautifulSoup(response.text, "html.parser")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_attempts - 1:
                print(f"Timeout/Network error ({e}). Retrying...")
                time.sleep(2)
                continue
            else:
                stats["failed_pages"] += 1
                return None
                
    stats["failed_pages"] += 1
    return None

def discover_books():
    current_url = START_URL
    book_links_with_source = []
    pages_visited = 0
    
    while current_url and pages_visited < 3:
        pages_visited += 1
        soup = get_soup_politely(current_url, f"catalogue-page-{pages_visited}.html")
        
        if not soup:
            break
            
        articles = soup.select("article.product_pod h3 a")
        for a in articles:
            absolute_url = urljoin(current_url, a.get("href"))
            book_links_with_source.append({
                "url": absolute_url,
                "source": current_url
            })
            
        next_button = soup.select_one("li.next a")
        if next_button:
            current_url = urljoin(current_url, next_button.get("href"))
        else:
            current_url = None

    unique_books = {book['url']: book for book in book_links_with_source}.values()
    return list(unique_books)

def extract_and_normalize(book_data):
    url = book_data["url"]
    source_page = book_data["source"]
    safe_filename = url.split("/")[-2] + ".html"
    
    soup = get_soup_politely(url, safe_filename)
    if not soup:
        return None, "Failed to fetch or parse detail page"
        
    product_main = soup.select_one("article.product_page")
    if not product_main:
        return None, "Product page container missing"
        
    title_el = product_main.select_one("h1")
    title = title_el.text if title_el else None
    
    price_el = product_main.select_one("p.price_color")
    price_text = price_el.text if price_el else ""
    
    cleaned_price_str = re.sub(r'[^\d.]', '', price_text)
    try:
        price_gbp = float(cleaned_price_str)
    except ValueError:
        price_gbp = 0.0
        
    avail_el = product_main.select_one("p.instock.availability")
    availability_text = avail_el.text.strip() if avail_el else None
    
    rating_el = product_main.select_one("p.star-rating")
    rating_text = rating_el["class"][1] if rating_el and len(rating_el["class"]) > 1 else None
    
    desc_el = product_main.select_one("#product_description")
    if desc_el:
        desc_p = desc_el.find_next_sibling("p")
        description = desc_p.text if desc_p else None
    else:
        description = None

    raw_dict = {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "price_gbp": price_gbp,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    try:
        validated_record = BookRecord(**raw_dict)
        return validated_record.model_dump(), None
    except ValidationError as e:
        return None, str(e)

def run_pipeline():
    start_time = time.time()
    start_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    os.makedirs("output", exist_ok=True)
    print("Discovering unique book URLs...")
    book_links = discover_books()
    
    # Prove it works: add one made-up book URL to your list on purpose[cite: 1]
    book_links.append({
        "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
        "source": "fake_test_injection"
    })
    
    print(f"Target scope acquired: {len(book_links)} items (including 1 fake test URL).")
    
    good_records = []
    error_records = []
    
    for book in book_links:
        record, error = extract_and_normalize(book)
        if record:
            good_records.append(record)
            stats["valid_records"] += 1
        else:
            error_records.append({"url": book["url"], "error": error})
            stats["invalid_records"] += 1
            
    # Save the output files
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(good_records, f, indent=2, ensure_ascii=False)
        
    if error_records:
        with open("output/errors.json", "w", encoding="utf-8") as f:
            json.dump(error_records, f, indent=2, ensure_ascii=False)
            
    # End every run by writing output/run-report.json with honest numbers[cite: 1]
    duration_seconds = round(time.time() - start_time, 2)
    report = {
        "start_time": start_time_iso,
        "duration_seconds": duration_seconds,
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": stats["valid_records"],
        "invalid_records": stats["invalid_records"],
        "failed_pages": stats["failed_pages"]
    }
    
    with open("output/run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    print("\n--- Run Complete ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run_pipeline()