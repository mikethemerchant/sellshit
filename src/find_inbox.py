"""
Try to get to the inbox list view
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Connect to existing Chrome
chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9222"
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Connected to Chrome")
print(f"Current URL: {driver.current_url}")

# Try clicking back or finding a way to the inbox list
print("\n📍 Trying to navigate to inbox list...")

# Method 1: Try pressing ESC to close current thread
try:
    from selenium.webdriver.common.action_chains import ActionChains
    actions = ActionChains(driver)
    actions.send_keys(Keys.ESCAPE).perform()
    time.sleep(2)
    print(f"After ESC: {driver.current_url}")
except Exception as e:
    print(f"ESC failed: {e}")

# Method 2: Look for a back button or inbox link
try:
    # Try to find and click "Messages" or "Chats" link
    possible_selectors = [
        "//a[@aria-label='Chats']",
        "//a[contains(text(), 'Chats')]",
        "//div[@aria-label='Chats']",
    ]
    for sel in possible_selectors:
        try:
            elem = driver.find_element(By.XPATH, sel)
            print(f"Found element with selector: {sel}")
            elem.click()
            time.sleep(3)
            print(f"After click: {driver.current_url}")
            break
        except:
            continue
except Exception as e:
    print(f"Click failed: {e}")

# Now try to find conversations
print("\n🔍 Looking for conversation rows...")
rows = driver.find_elements(By.XPATH, "//div[@role='row']")
print(f"Found {len(rows)} rows")

for i, row in enumerate(rows[:10]):
    try:
        text = (row.text or '').strip().replace('\n', ' ')[:100]
        # Look for links within the row
        links = row.find_elements(By.XPATH, ".//a[contains(@href, '/messages/t/')]")
        href = links[0].get_attribute('href')[-30:] if links else "no link"
        print(f"  [{i}] {text} | {href}")
    except Exception as e:
        print(f"  [{i}] Error: {e}")

print("\n✅ Done")
