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

# Configure logging to track scraper activity
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class KauflandScraper:
    def __init__(self, base_url, search_terms):
        """
        Initializes the KauflandScraper with a base search URL and search terms.

        Args:
            base_url (str): The search URL template where keywords are inserted.
            search_terms (list): A list of search terms to query.
        """
        self.base_url = base_url
        self.search_terms = search_terms
        self.output_dir = "output/kaufland/downloaded_html"  # Directory for saving HTML files
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure output directory exists

    def setup_driver(self):
        """
        Configures and initializes the Selenium WebDriver.

        Returns:
            webdriver.Chrome: A configured Selenium WebDriver instance.
        """
        options = Options()
        options.add_argument("--start-maximized")  # Open in maximized mode
        options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
        )  # Mimic a real browser
        options.add_argument("--disable-dev-shm-usage")  # Overcome limited resources in containers
        options.add_argument("--no-sandbox")  # Required for running in some environments

        service = Service(ChromeDriverManager().install())  # Automatically install ChromeDriver
        return webdriver.Chrome(service=service, options=options)

    def accept_cookies(self, driver):
        """
        Handles cookie banners if they appear on the page.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Akzeptieren')]"))
            )
            cookie_button.click()
            logging.info("Accepted cookies.")
        except Exception:
            logging.info("No cookie banner detected.")

    def scrape_search_terms(self):
        """
        Iterates through search terms, scrapes each search results page, and saves the HTML.
        """
        for term in self.search_terms:
            driver = self.setup_driver()  # Start a new browser session for each term
            try:
                url = self.base_url.format(term)  # Generate search URL
                logging.info(f"Accessing URL: {url}")
                driver.get(url)

                # Accept cookies if prompted
                self.accept_cookies(driver)

                # Wait for the page to fully load
                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logging.info("Page loaded successfully.")

                # Save the page's HTML content
                html_content = driver.page_source
                file_name = term.replace("%20", "_").replace(",", "") + ".html"  # Format file name
                file_path = os.path.join(self.output_dir, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logging.info(f"Page for '{term}' saved to {file_path}")

                # Introduce a small delay to mimic human behavior and avoid detection
                time.sleep(5)

            except Exception as e:
                logging.error(f"An error occurred for term '{term}': {e}")

            finally:
                driver.quit()  # Close the browser session after scraping each term

    def run(self):
        """
        Runs the scraper by iterating over all search terms.
        """
        try:
            self.scrape_search_terms()
            logging.info("Kaufland scraping process completed successfully.")
        except Exception as e:
            logging.error(f"Scraper encountered an error: {e}")
