import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging to track the scraper's process
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class AldiScraper:
    def __init__(self, static_urls, dynamic_base_url, keywords):
        """
        Initializes the AldiScraper with static URLs, a dynamic base URL for searches, and keywords.

        Args:
            static_urls (list): A list of predefined URLs to scrape.
            dynamic_base_url (str): Base URL used for searching with keywords.
            keywords (list): List of keywords to use for generating search URLs.
        """
        self.static_urls = static_urls
        self.dynamic_base_url = dynamic_base_url
        self.keywords = keywords
        self.output_dir = "output/aldi/downloaded_html"  # Directory where scraped HTML files will be stored
        os.makedirs(self.output_dir, exist_ok=True)  # Ensure the output directory exists

    def setup_driver(self):
        """
        Configures and initializes the Selenium WebDriver.

        Returns:
            webdriver.Chrome: A configured Selenium WebDriver instance.
        """
        options = Options()
        options.add_argument("--start-maximized")  # Open browser in maximized mode
        options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
        options.add_argument("--disable-dev-shm-usage")  # Overcome limited resources in containers
        options.add_argument("--no-sandbox")  # Required for running in some environments
        options.add_argument("--headless")  # Run in the background (no browser window)

        service = Service(ChromeDriverManager().install())  # Use WebDriver Manager for automatic ChromeDriver updates
        return webdriver.Chrome(service=service, options=options)

    def save_html(self, driver, url, file_name):
        """
        Fetches a webpage and saves its HTML content.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
            url (str): The webpage URL to fetch.
            file_name (str): Name of the file to save the HTML content.
        """
        try:
            logging.info(f"Accessing URL: {url}")
            driver.get(url)  # Open the URL in the browser

            # Wait until the page is fully loaded
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logging.info("Page loaded successfully.")

            # Save the HTML content to a file
            html_content = driver.page_source
            file_path = os.path.join(self.output_dir, file_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logging.info(f"Page saved to {file_path}")

        except Exception as e:
            logging.error(f"Failed to load URL {url}: {e}")

    def scrape_static_urls(self, driver):
        """
        Scrapes all predefined (static) URLs.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        for url in self.static_urls:
            file_name = url.split("/")[-1].split("?")[0] + ".html"  # Generate a filename from the URL
            self.save_html(driver, url, file_name)

    def scrape_dynamic_urls(self, driver):
        """
        Generates and scrapes URLs using keywords.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        for keyword in self.keywords:
            query_url = self.dynamic_base_url.format(keyword)  # Insert keyword into the search URL
            file_name = keyword.replace("%20", "_") + ".html"  # Replace spaces for filename compatibility
            self.save_html(driver, query_url, file_name)

    def run(self):
        """
        Executes the scraping process: 
        - Initializes the WebDriver
        - Scrapes both static and dynamic URLs
        - Closes the WebDriver after completion
        """
        driver = self.setup_driver()
        try:
            logging.info("Starting Aldi scraping process...")

            # Step 1: Scrape static URLs
            self.scrape_static_urls(driver)

            # Step 2: Scrape dynamic URLs based on keywords
            self.scrape_dynamic_urls(driver)

            logging.info("Aldi scraping completed successfully.")

        except Exception as e:
            logging.error(f"An error occurred during scraping: {e}")

        finally:
            driver.quit()  # Always close the browser after scraping
            logging.info("WebDriver closed.")
