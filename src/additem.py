from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time

# Load credentials
load_dotenv()
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASS = os.getenv("FB_PASS")

# Optional: set these in your environment (or .env) to reuse a real Chrome profile
# Example (Windows):
# CHROME_USER_DATA_DIR=C:\\Users\\<You>\\AppData\\Local\\Google\\Chrome\\User Data
# CHROME_PROFILE_DIR=Profile 2
CHROME_USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR")
CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR")

# Setup Chrome
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")

# If you provide a Chrome user data dir and profile, Selenium will reuse that profile
if CHROME_USER_DATA_DIR:
	options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
if CHROME_PROFILE_DIR:
	options.add_argument(f"--profile-directory={CHROME_PROFILE_DIR}")

# Reduce automation flags (helps but doesn't guarantee bypassing detection)
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Optional: attempt to hide webdriver property in JS context (may help)
try:
	driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
		'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
	})
except Exception:
	# Not critical; continue without failing
	pass

# Go to Facebook
driver.get("https://www.facebook.com")

# Log in
time.sleep(3)
email_input = driver.find_element(By.ID, "email")
pass_input = driver.find_element(By.ID, "pass")

email_input.send_keys(FB_EMAIL)
pass_input.send_keys(FB_PASS)
pass_input.send_keys(Keys.RETURN)

# Wait and navigate to Marketplace
time.sleep(10)
driver.get("https://www.facebook.com/marketplace/create/item")

# Keep the browser open for inspection
input("Press Enter to quit...")
driver.quit()
