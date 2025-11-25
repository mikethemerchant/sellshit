"""
Find Antonio's conversation about Rich Dad Poor Dad
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

print(f"Current URL: {driver.current_url}")

# Find all conversation rows
print("\n🔍 Scanning all conversation rows...")
rows = driver.find_elements(By.XPATH, "//div[@role='row']")
print(f"Found {len(rows)} rows total\n")

# Known thread IDs from buyer_state.json
known_threads = [
    "1476401086986855",  # Alex
    "3509688825837712",  # WiFi
    "1058253483035875",  # Pisit
    "1745768319324111",  # Chris
    "1187271722897711",  # Patch
]

antonio_candidates = []

for i, row in enumerate(rows):
    try:
        text = (row.text or '').strip().replace('\n', ' ')
        
        # Look for links within the row
        links = row.find_elements(By.XPATH, ".//a[contains(@href, '/messages/t/')]")
        if not links:
            continue
            
        href = links[0].get_attribute('href') or ''
        
        # Extract thread ID from href
        thread_id = None
        if '/messages/t/' in href:
            parts = href.split('/messages/t/')
            if len(parts) > 1:
                thread_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
        
        # Check if this is a known thread
        is_known = thread_id in known_threads if thread_id else False
        
        # Check for "Rich Dad" or "Poor Dad" or "Antonio" in text
        has_rich_dad = 'rich dad' in text.lower() or 'poor dad' in text.lower()
        has_antonio = 'antonio' in text.lower()
        
        # Check for unread indicators
        has_unread_text = 'new message' in text.lower()
        
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
        
        # If it matches our criteria, add to candidates
        if (has_rich_dad or has_antonio or (not is_known and has_blue_dot)):
            antonio_candidates.append({
                'index': i,
                'thread_id': thread_id,
                'text': text[:150],
                'is_known': is_known,
                'has_rich_dad': has_rich_dad,
                'has_antonio': has_antonio,
                'has_blue_dot': has_blue_dot,
                'has_unread_text': has_unread_text,
                'element': row
            })
            
    except Exception as e:
        continue

print(f"🎯 Found {len(antonio_candidates)} potential Antonio conversations:\n")
for cand in antonio_candidates:
    print(f"[{cand['index']}] Thread: {cand['thread_id']}")
    print(f"    Known: {cand['is_known']} | RichDad: {cand['has_rich_dad']} | Antonio: {cand['has_antonio']}")
    print(f"    BlueDot: {cand['has_blue_dot']} | UnreadText: {cand['has_unread_text']}")
    print(f"    Text: {cand['text']}")
    print()

# If we found Antonio, click it
if antonio_candidates:
    best = antonio_candidates[0]
    print(f"✅ Clicking best candidate at index {best['index']}...")
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", best['element'])
        time.sleep(1)
        link = best['element'].find_element(By.XPATH, ".//a[contains(@href, '/messages/t/')]")
        link.click()
        time.sleep(4)
        print(f"📍 New URL: {driver.current_url}")
    except Exception as e:
        print(f"❌ Click failed: {e}")
else:
    print("❌ No Antonio candidates found")

print("\n✅ Done")
