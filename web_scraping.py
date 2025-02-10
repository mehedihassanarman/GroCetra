import json
from src.penny_scraper import PennyScraper
from src.netto_scraper import NettoScraper
from src.aldi_scraper import AldiScraper
from src.rewe_scraper import ReweScraper
from src.kaufland_scraper import KauflandScraper

# Function to load the scraping directions (URLs, keywords, etc.) from directions.txt
def load_directions():
    with open("directions.txt", "r") as f:
        return json.load(f)

def main():
    # Load all scraping instructions
    directions = load_directions()
    
    # Run Penny Scraper
    print("Running Penny Scraper...")
    scraper = PennyScraper()
    downloaded_file = scraper.download_page()
    if downloaded_file:
        print(f"Penny: Downloading complete. HTML file saved at: {downloaded_file}")
    else:
        print("Penny: Failed to download the page.")
    
    # Run Netto Scraper
    print("Running Netto Scraper...")
    netto_data = directions["netto"]
    scraper = NettoScraper(netto_data["base_url"], netto_data["keywords"], netto_data["static_urls"])
    scraper.run()
    
    # Run Aldi Scraper
    print("Running Aldi Scraper...")
    aldi_data = directions["aldi"]
    scraper = AldiScraper(aldi_data["static_urls"], aldi_data["keyword_url"], aldi_data["search_terms"])
    scraper.run()
    
    # Run Rewe Scraper
    print("Running Rewe Scraper...")
    rewe_data = directions["rewe"]
    scraper = ReweScraper(rewe_data["base_url"], rewe_data["search_terms"])
    scraper.run()
    
    # Run Kaufland Scraper
    print("Running Kaufland Scraper...")
    kaufland_data = directions["kaufland"]
    scraper = KauflandScraper(kaufland_data["base_url"], kaufland_data["search_terms"])
    scraper.run()
    
    # All scrapers have completed their tasks
    print("All scrapers completed.")

# Standard Python script entry point
if __name__ == "__main__":
    main()
