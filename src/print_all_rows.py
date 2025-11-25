"""
Print ALL conversation rows to find Antonio
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

# Navigate and wait
driver.get("https://www.facebook.com/messages")
time.sleep(8)

# Press ESC to ensure we're in list view
from selenium.webdriver.common.action_chains import ActionChains
actions = ActionChains(driver)
actions.send_keys(Keys.ESCAPE).perform()
time.sleep(2)

print(f"Current URL: {driver.current_url}\n")

# Find all conversation rows
rows = driver.find_elements(By.XPATH, "//div[@role='row']")
print(f"Found {len(rows)} rows total")

# Open output file
output_file = open("conversation_rows.txt", "w", encoding="utf-8")
output_file.write(f"Found {len(rows)} rows total\n")
output_file.write("="*100 + "\n\n")

# Known thread IDs
known_threads = {
    "1476401086986855": "Alex",
    "3509688825837712": "WiFi",
    "1058253483035875": "Pisit",
    "1745768319324111": "Chris",
    "1187271722897711": "Patch",
}

for i, row in enumerate(rows):
    try:
        text = (row.text or '').strip().replace('\n', ' ')
        
        # Look for links within the row
        links = row.find_elements(By.XPATH, ".//a[contains(@href, '/messages/t/')]")
        if not links:
            output_file.write(f"[{i}] NO LINK | {text[:100]}\n")
            continue
            
        href = links[0].get_attribute('href') or ''
        
        # Extract thread ID
        thread_id = None
        if '/messages/t/' in href:
            parts = href.split('/messages/t/')
            if len(parts) > 1:
                thread_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
        
        # Check if known
        buyer_name = known_threads.get(thread_id, "UNKNOWN")
        
        # Check for blue dot
        has_blue_dot = False
        try:
            dots = row.find_elements(By.XPATH, ".//div | .//span")
            for dot in dots[:10]:
                bg = driver.execute_script("return window.getComputedStyle(arguments[0]).backgroundColor;", dot)
                if bg and 'rgb' in bg.lower():
                    import re
                    match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)', bg)
                    if match:
                        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        if r < 50 and b > 200:
                            has_blue_dot = True
                            break
        except:
            pass
        
        dot_indicator = "🔵" if has_blue_dot else "⚪"
        output_file.write(f"\n[{i}] {dot_indicator} {buyer_name} | Thread: {thread_id}\n")
        output_file.write(f"    Text: {text[:200]}\n")
        
    except Exception as e:
        output_file.write(f"[{i}] ERROR: {e}\n")

output_file.write("\n" + "="*100 + "\n")
output_file.close()

print("✅ Output saved to conversation_rows.txt")
