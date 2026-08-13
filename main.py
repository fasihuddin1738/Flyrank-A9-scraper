#USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"
import os
import time
import requests
import json
from urllib.parse import urljoin
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# Constants
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"

def get_soup_politely(url, cache_filename):
    """Fetches a page politely and uses a specific filename for the cache."""
    os.makedirs("cache", exist_ok=True)
    cache_file = os.path.join("cache", cache_filename)
    
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        # Wait at least half a second between real requests
        time.sleep(0.5) 
        headers = {"User-Agent": USER_AGENT}
        # Timeout and status check
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None
            
        html = response.text
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html)
            
    return BeautifulSoup(html, "html.parser")

def discover_books():
    """Discovers the 60 book URLs from the first 3 catalogue pages."""
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
            # Keep track of the source page for provenance[cite: 1]
            book_links_with_source.append({
                "url": absolute_url,
                "source": current_url
            })
            
        next_button = soup.select_one("li.next a")
        if next_button:
            current_url = urljoin(current_url, next_button.get("href"))
        else:
            current_url = None

    # Remove duplicate links based on URL[cite: 1]
    unique_books = {book['url']: book for book in book_links_with_source}.values()
    return list(unique_books)

def extract_book_details(book_data):
    """Extracts raw text fields from a single book detail page."""
    url = book_data["url"]
    source_page = book_data["source"]
    
    # Generate a safe cache filename based on the URL
    safe_filename = url.split("/")[-2] + ".html"
    
    # Fetch and cache each detail page with the same politeness[cite: 1]
    soup = get_soup_politely(url, safe_filename)
    if not soup:
        return None
        
    # Aim selectors at the product area, not the whole document[cite: 1]
    product_main = soup.select_one("article.product_page")
    if not product_main:
        return None
        
    # Extract title
    title_el = product_main.select_one("h1")
    title = title_el.text if title_el else None
    
    # Extract price
    price_el = product_main.select_one("p.price_color")
    price_text = price_el.text if price_el else None
    
    # Extract availability
    avail_el = product_main.select_one("p.instock.availability")
    availability_text = avail_el.text.strip() if avail_el else None
    
    # Extract rating
    rating_el = product_main.select_one("p.star-rating")
    rating_text = rating_el["class"][1] if rating_el and len(rating_el["class"]) > 1 else None
    
    # Extract description
    desc_el = product_main.select_one("#product_description")
    if desc_el:
        desc_p = desc_el.find_next_sibling("p")
        description = desc_p.text if desc_p else None
    else:
        # Some books have no description. Store null[cite: 1]
        description = None

    # Return the raw record with all eight keys[cite: 1]
    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }

def run_scraper():
    print("Discovering book URLs...")
    book_links = discover_books()
    
    print(f"Discovered {len(book_links)} unique URLs. Extracting details...")
    
    raw_records = []
    for book in book_links:
        record = extract_book_details(book)
        if record:
            raw_records.append(record)
            
    if raw_records:
        # Print one complete raw record[cite: 1]
        print("\n--- Sample Raw Record ---")
        print(json.dumps(raw_records[0], indent=2))
        
    # Print the summary detail_pages=60[cite: 1]
    print(f"\ndetail_pages={len(raw_records)}")

if __name__ == "__main__":
    run_scraper()