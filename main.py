import os
import requests

# Constants
URL = "https://books.toscrape.com/catalogue/page-1.html"
CACHE_FILE = "cache/catalogue-page-1.html"
USER_AGENT = "FlyRankInternship_A9/1.0 (+https://github.com/fasihuddin1738/Flyrank-A9-scraper)"

def fetch_and_cache():
    """Fetches a web page politely and caches it locally."""
    # Ensure the cache directory exists
    os.makedirs("cache", exist_ok=True)

    # 1. Check if we already have the file (The Cache)
    if os.path.exists(CACHE_FILE):
        print("CACHE HIT")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            html = f.read()
            
    # 2. If not, go fetch it politely
    else:
        print("FETCH")
        headers = {"User-Agent": USER_AGENT}
        
        # Always set a timeout
        response = requests.get(URL, headers=headers, timeout=10)
        
        # Always check the status code before proceeding
        if response.status_code != 200:
            print(f"Failed to fetch page. Status code: {response.status_code}")
            return
            
        html = response.text
        
        # Save to cache so we don't have to fetch it again
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(html)
            
    # 3. Report the size (never dump the whole HTML to the terminal)[cite: 1]
    print(f"Response size: {len(html)} characters")

if __name__ == "__main__":
    fetch_and_cache()