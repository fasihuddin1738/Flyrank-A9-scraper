import os
import time
import requests
from urllib.parse import urljoin
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup

# Constants
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"

def get_soup_politely(url, page_num):
    """Fetches a page, uses cache if available, delays real requests, and returns parsed HTML."""
    os.makedirs("cache", exist_ok=True)
    cache_file = f"cache/catalogue-page-{page_num}.html"
    
    if os.path.exists(cache_file):
        # Cached pages need no delay
        with open(cache_file, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        # Wait at least half a second between real requests to the site
        time.sleep(0.5) 
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None
            
        html = response.text
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(html)
            
    # Parse the saved page with Beautiful Soup[cite: 1]
    return BeautifulSoup(html, "html.parser")

def discover_books():
    current_url = START_URL
    book_urls = []
    pages_visited = 0
    
    # Follow the catalogue's own "next" link to page 2, then page 3, then stop[cite: 1]
    while current_url and pages_visited < 3:
        pages_visited += 1
        soup = get_soup_politely(current_url, pages_visited)
        
        if not soup:
            break
            
        # Collect the link to every book on the current page[cite: 1]
        articles = soup.select("article.product_pod h3 a")
        for a in articles:
            href = a.get("href")
            # Turn each one into an absolute URL using urljoin[cite: 1]
            absolute_url = urljoin(current_url, href)
            book_urls.append(absolute_url)
            
        # Find the 'next' link
        next_button = soup.select_one("li.next a")
        if next_button:
            next_href = next_button.get("href")
            current_url = urljoin(current_url, next_href)
        else:
            current_url = None

    # Remove duplicate links before the next stage[cite: 1]
    unique_urls = list(set(book_urls))
    
    print(f"catalogue_pages={pages_visited}")
    print(f"discovered={len(book_urls)}")
    print(f"unique_urls={len(unique_urls)}")

if __name__ == "__main__":
    discover_books()