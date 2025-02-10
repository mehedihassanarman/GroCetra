import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging for better debugging and tracking
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class NettoScraper:
    def __init__(self, base_url, keywords, static_urls):
        """
        Initializes the NettoScraper with necessary parameters.

        Args:
            base_url (str): The base URL for keyword searches.
            keywords (list): A list of search terms to query.
            static_urls (list): A list of predefined URLs to scrape.
        """
        self.base_url = base_url
        self.keywords = keywords
        self.static_urls = static_urls
        self.output_dir = "output/netto/downloaded_html"  # Directory for saving HTML files
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure output directory exists

    def setup_driver(self):
        """
        Configures and initializes the Selenium WebDriver.

        Returns:
            webdriver.Chrome: A configured Selenium WebDriver instance.
        """
        options = Options()
        options.add_argument("--incognito")  # Open browser in incognito mode
        options.add_argument("--start-maximized")  # Start with maximized window
        options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
        options.add_argument("--no-sandbox")  # Required for running in some environments

        service = Service(ChromeDriverManager().install())  # Automatically install ChromeDriver
        return webdriver.Chrome(service=service, options=options)

    def accept_cookies(self, driver, timeout=10):
        """
        Handles cookie banners if they appear on the page.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
            timeout (int): Max time to wait for the cookie banner.
        """
        try:
            cookie_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Akzeptieren') or contains(text(),'Accept')]")
                )
            )
            cookie_button.click()
            logging.info("Accepted cookies.")
        except Exception:
            logging.info("No cookie banner detected or timed out waiting for it.")

    def select_store_interactively(self, driver, postal_code="12345"):
        """
        Selects a store by entering a postal code in the Filialfinder.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
            postal_code (str): The ZIP code for finding a store.
        """
        driver.get("https://www.netto-online.de/filialfinder")
        self.accept_cookies(driver)

        try:
            store_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@id='StoreSearch']"))
            )
            store_input.clear()
            store_input.send_keys(postal_code)
        except Exception:
            logging.error("Could not find the store search input field.")
            return

        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Suchen')]"))
            )
            search_button.click()
            logging.info(f"Searched for postal code: {postal_code}")
        except Exception:
            logging.error("Could not find the search button.")
            return

        try:
            first_store_result = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='storeSearchResults']//a"))
            )
            first_store_result.click()
            logging.info("Selected the first store from search results.")
        except Exception:
            logging.error("Could not select the store from the search results.")
            return

        time.sleep(2)
        logging.info("Store should now be selected.")

    def scrape_static_pages(self, driver):
        """
        Scrapes all predefined static pages and saves their HTML content.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        for url in self.static_urls:
            try:
                logging.info(f"Accessing static URL: {url}")
                driver.get(url)
                self.accept_cookies(driver)

                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )

                # Save the HTML content
                html_content = driver.page_source
                safe_filename = "".join(char if char.isalnum() else "_" for char in url)
                file_name = f"{safe_filename}.html"
                file_path = os.path.join(self.output_dir, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logging.info(f"Saved static page to {file_path}")
                time.sleep(2)  # Pause between requests
            except Exception as e:
                logging.error(f"Error scraping static URL '{url}': {e}")

    def scrape_keywords(self, driver):
        """
        Scrapes pages using keyword searches and saves their HTML content.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        for keyword in self.keywords:
            try:
                formatted_keyword = "+".join(keyword.split())  # Format keyword for search URL
                url = self.base_url.format(formatted_keyword)
                logging.info(f"Accessing URL: {url}")
                driver.get(url)

                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )

                # Save the HTML content
                html_content = driver.page_source
                file_name = keyword.replace(" ", "_") + ".html"
                file_path = os.path.join(self.output_dir, file_name)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logging.info(f"Saved page for '{keyword}' to {file_path}")
                time.sleep(2)  # Pause to avoid detection
            except Exception as e:
                logging.error(f"Error scraping keyword '{keyword}': {e}")

    def run(self):
        """
        Runs the scraper by:
        1. Selecting a store
        2. Scraping static pages
        3. Scraping keyword-based search pages
        """
        driver = self.setup_driver()
        try:
            self.select_store_interactively(driver, postal_code="12345")
            self.scrape_static_pages(driver)
            self.scrape_keywords(driver)
            logging.info("Netto scraping process completed successfully.")
        except Exception as e:
            logging.error(f"Scraper encountered an error: {e}")
        finally:
            driver.quit()  # Ensure the browser session is closed
