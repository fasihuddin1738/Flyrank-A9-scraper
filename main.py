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
from pydantic import BaseModel, Field, ValidationError

# Constants
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"

class BookRecord(BaseModel):
    """Pydantic schema defining the strict shape of a validated book record."""
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
    """Fetches a page politely and uses a specific filename for the cache."""
    os.makedirs("cache", exist_ok=True)
    cache_file = os.path.join("cache", cache_filename)
    
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        time.sleep(0.5) 
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None
            
        html = response.text
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html)
            
    return BeautifulSoup(html, "html.parser")

def discover_books():
    """Discovers unique book URLs from the first 3 catalogue pages using canonical identity."""
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

    # Use the absolute product_url as canonical identity to remove duplicates
    unique_books = {book['url']: book for book in book_links_with_source}.values()
    return list(unique_books)

def extract_and_normalize(book_data):
    """Extracts raw data, normalizes types, and validates against the Pydantic schema."""
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
    
    # Normalize price_text ("£51.77") into price_gbp (51.77)
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

    # Validate every record against the Pydantic schema
    try:
        validated_record = BookRecord(**raw_dict)
        return validated_record.model_dump(), None
    except ValidationError as e:
        return None, str(e)

def run_pipeline():
    os.makedirs("output", exist_ok=True)
    print("Discovering unique book URLs...")
    book_links = discover_books()
    print(f"Target scope acquired: {len(book_links)} unique items.")
    
    good_records = []
    error_records = []
    
    for book in book_links:
        record, error = extract_and_normalize(book)
        if record:
            good_records.append(record)
        else:
            error_records.append({
                "url": book["url"],
                "error": error
            })
            
    # Write good records idempotently to output/books.json
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(good_records, f, indent=2, ensure_ascii=False)
        
    # Write any failed validations to errors.json[cite: 1]
    if error_records:
        with open("output/errors.json", "w", encoding="utf-8") as f:
            json.dump(error_records, f, indent=2, ensure_ascii=False)
            
    print(f"\nPipeline Execution Complete:")
    print(f" - Valid records stored: {len(good_records)}")
    print(f" - Quarantined errors: {len(error_records)}")

if __name__ == "__main__":
    run_pipeline()