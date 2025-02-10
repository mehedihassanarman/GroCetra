import json
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ReweScraper:
    def __init__(self, base_url, search_terms):
        """
        Initializes the ReweScraper with a base URL and search terms.

        Args:
            base_url (str): The base search URL where search terms will be inserted.
            search_terms (list): A list of keywords to search for on the Rewe website.
        """
        self.base_url = base_url
        self.search_terms = search_terms
        self.output_dir = "output/rewe/downloaded_html"  # Directory where HTML files will be saved
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure that the output directory exists

    def setup_driver(self):
        """
        Configures and initializes the Selenium WebDriver.

        Returns:
            webdriver.Chrome: A Selenium WebDriver instance configured with necessary options.
        """
        options = Options()
        options.add_argument("--start-maximized")  # Open browser in maximized mode
        options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
        options.add_argument("--no-sandbox")  # Required for running in certain environments
        options.add_argument("--disable-gpu")  # Disable GPU rendering for stability
        options.add_argument("--disable-dev-shm-usage")  # Optimize memory usage

        service = Service(ChromeDriverManager().install())  # Install the ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)

        # Load saved cookies if available
        if os.path.exists("rewe_cookies.json"):
            driver.get("https://shop.rewe.de/")  # Open Rewe homepage before loading cookies
            with open("rewe_cookies.json", "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)  # Add each cookie to the browser session

        return driver

    def wait_for_page_load(self, driver):
        """
        Waits until the page is fully loaded.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        try:
            # Wait until the browser signals that the page is fully loaded
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(5)  # Extra delay to allow content to load
        except Exception as e:
            logging.warning(f"Page load timeout or error: {e}")

    def scrape_page(self, url, file_name):
        """
        Scrapes a single page and saves its HTML content to a file.

        Args:
            url (str): The webpage URL to scrape.
            file_name (str): The filename where the scraped HTML will be saved.
        """
        driver = self.setup_driver()  # Start the browser
        try:
            driver.get(url)  # Open the URL
            self.wait_for_page_load(driver)  # Ensure the page loads fully before proceeding

            # Save the page's HTML content
            file_path = os.path.join(self.output_dir, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)  # Write the HTML content to the file

        except Exception as e:
            logging.error(f"Error scraping URL {url}: {e}")

        finally:
            driver.quit()  # Close the browser after scraping

    def scrape_search_terms(self):
        """
        Iterates through search terms, scrapes each search results page, and saves the HTML.
        """
        for term in self.search_terms:
            formatted_term = term.replace(" ", "%20")  # Convert spaces to URL-friendly format
            url = self.base_url.format(formatted_term)  # Generate the search query URL
            file_name = f"{term.replace(' ', '_')}.html"  # Format the filename to avoid spaces
            self.scrape_page(url, file_name)  # Scrape and save the page

    def run(self):
        """
        Runs the scraper by iterating over all search terms and scraping their pages.
        """
        try:
            self.scrape_search_terms()  # Perform search-based scraping
        except Exception as e:
            logging.error(f"Scraper encountered an error: {e}")
