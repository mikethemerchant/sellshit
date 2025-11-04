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

# Setup Chrome
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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
