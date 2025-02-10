import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class PennyScraper:
    def __init__(self):
        self.base_url = "https://www.penny.de/angebote/15A-05-66"
        self.output_dir = "output/penny"
        self.html_dir = os.path.join(self.output_dir, "downloaded_html")
        os.makedirs(self.html_dir, exist_ok=True)

    def _setup_driver(self):
        """Set up the Selenium WebDriver with predefined cookies to bypass popups."""
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # ✅ Pretend to be a normal user with a real browser
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # ✅ Load page once to manually set cookies (only needed once)
        driver.get("https://www.penny.de/")
        time.sleep(2)

        # ✅ Add cookies manually to trick Penny.de into thinking we accepted cookies
        driver.add_cookie({"name": "cookie_consent", "value": "accepted", "domain": ".penny.de"})
        driver.add_cookie({"name": "session", "value": "fake_session_value", "domain": ".penny.de"})

        return driver

    def download_page(self):
        """Download the HTML without triggering the cookie popup."""
        driver = self._setup_driver()
        try:
            print(f"Attempting to download: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(3)  # Allow time for page to load

            # ✅ Ensure cookies are in place before reloading
            driver.refresh()
            time.sleep(3)

            # ✅ Final verification: Check if page is valid
            if "404" in driver.title or len(driver.page_source) < 1000:
                print(f"⚠ Warning: Page at {self.base_url} might not have loaded correctly.")
                return None

            # ✅ Save the HTML page
            html = driver.page_source
            filename = os.path.join(self.html_dir, "penny_offers.html")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"✅ Successfully saved: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error while processing {self.base_url}: {str(e)}")
            return None
        finally:
            driver.quit()
