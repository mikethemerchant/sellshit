"""
Broader scan to understand the DOM structure
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Connect to existing Chrome
chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9222"
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Connected to Chrome")
print(f"Current URL: {driver.current_url}")

# Navigate to messages inbox
print("\n📍 Navigating to messages inbox...")
driver.get("https://www.facebook.com/messages")
time.sleep(10)

print(f"New URL: {driver.current_url}")

# Try multiple selectors
selectors = [
    ("Links with /messages/t/", "//a[contains(@href, '/messages/t/')]"),
    ("Links with role=link", "//a[@role='link']"),
    ("Divs with role=row", "//div[@role='row']"),
    ("Divs with role=listitem", "//div[@role='listitem']"),
    ("All links", "//a"),
]

for name, xpath in selectors:
    try:
        elements = driver.find_elements(By.XPATH, xpath)
        print(f"\n{name}: Found {len(elements)} elements")
        for i, el in enumerate(elements[:5]):
            try:
                text = (el.text or '').strip().replace('\n', ' ')[:80]
                href = (el.get_attribute('href') or '')[-50:]
                print(f"  [{i}] {text} | {href}")
            except:
                pass
    except Exception as e:
        print(f"{name}: Error - {e}")

print("\n✅ Done")
