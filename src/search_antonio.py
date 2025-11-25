"""
Search for Antonio's thread by scrolling through the sidebar
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

# Refresh the page to ensure we see latest state
print("🔄 Refreshing page...")
driver.refresh()
time.sleep(5)

print(f"Current URL: {driver.current_url}\n")

# Try to find the Chats container and scroll to load more conversations
try:
    chats_container = driver.find_element(By.XPATH, "//div[@aria-label='Chats']")
    print("✅ Found Chats container")
    
    # Scroll down several times to load more conversations
    print("📜 Scrolling to load more conversations...")
    for i in range(5):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", chats_container)
        time.sleep(1)
    
    # Now look for all rows
    rows = chats_container.find_elements(By.XPATH, ".//div[@role='row']")
    print(f"Found {len(rows)} rows after scrolling\n")
    
    known_threads = {
        "1476401086986855": "Alex",
        "3509688825837712": "WiFi",
        "1058253483035875": "Pisit",
        "1745768319324111": "Chris",
        "1187271722897711": "Patch",
    }
    
    output_file = open("all_sidebar_rows.txt", "w", encoding="utf-8")
    output_file.write(f"Found {len(rows)} rows in sidebar\n")
    output_file.write("="*100 + "\n\n")
    
    for i, row in enumerate(rows):
        try:
            text = (row.text or '').strip().replace('\n', ' ')
            
            # Look for links
            links = row.find_elements(By.XPATH, ".//a[contains(@href, '/messages/t/')]")
            
            if links:
                href = links[0].get_attribute('href') or ''
                # Extract thread ID
                thread_id = None
                if '/messages/t/' in href:
                    parts = href.split('/messages/t/')
                    if len(parts) > 1:
                        thread_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
                
                buyer_name = known_threads.get(thread_id, "UNKNOWN - MIGHT BE ANTONIO!")
                
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
                
                # If this is unknown and has blue dot, it might be Antonio!
                if buyer_name.startswith("UNKNOWN") and has_blue_dot:
                    print(f"🎯 POTENTIAL ANTONIO at index {i}!")
                    print(f"   Thread: {thread_id}")
                    print(f"   Text: {text[:150]}")
            else:
                output_file.write(f"[{i}] NO LINK | {text[:150]}\n")
                
        except Exception as e:
            output_file.write(f"[{i}] ERROR: {e}\n")
    
    output_file.write("\n" + "="*100 + "\n")
    output_file.close()
    print("\n✅ Output saved to all_sidebar_rows.txt")
    
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n✅ Done")
