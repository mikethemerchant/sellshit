from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
options.debugger_address = "127.0.0.1:9222"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

driver.get("https://www.facebook.com/marketplace")
time.sleep(2)

selectors = [
    (By.XPATH, "//span[normalize-space()='Create new listing']"),
    (By.XPATH, "//div[.//text()[normalize-space()='Create new listing']]"),
    (By.XPATH, "//button[.//text()[contains(., 'Create new listing')]]"),
]

clicked = False
for by, sel in selectors:
    try:
        print("Trying selector:", sel)
        elem = wait.until(EC.element_to_be_clickable((by, sel)))
        print("Found element text:", elem.text)
        driver.execute_script("arguments[0].scrollIntoView(true);", elem)
        time.sleep(1)
        # try real browser click first
        driver.execute_script("arguments[0].click();", elem)
        print("✅ Clicked using JS injection:", sel)
        clicked = True
        break
    except Exception as e:
        print("Selector failed:", sel, "-", e)
        continue

if not clicked:
    print("❌ Could not find or click the Create new listing button")

time.sleep(3)
