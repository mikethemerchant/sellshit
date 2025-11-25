"""
Click the Marketplace aggregate and see what's inside
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

# Find and click the Marketplace aggregate row
print("\n🔍 Looking for Marketplace aggregate row...")
try:
    chats_container = driver.find_element(By.XPATH, "//div[@aria-label='Chats']")
    rows = chats_container.find_elements(By.XPATH, ".//div[@role='row']")
    
    for row in rows:
        text = (row.text or '').lower()
        if 'marketplace' in text:
            print(f"✅ Found Marketplace row: {row.text[:100]}")
            driver.execute_script("arguments[0].scrollIntoView();", row)
            time.sleep(0.5)
            
            # Try to find and click a link within the row
            try:
                link = row.find_element(By.XPATH, ".//a[@role='link']")
                driver.execute_script("arguments[0].click();", link)
                print("✅ Clicked Marketplace row via link")
            except:
                driver.execute_script("arguments[0].click();", row)
                print("✅ Clicked Marketplace row directly")
            
            time.sleep(5)
            break
except Exception as e:
    print(f"❌ Failed to click Marketplace row: {e}")

print(f"\nAfter click URL: {driver.current_url}")

# Now look for conversation threads in the main area
print("\n🔍 Looking for individual threads in main area...")
try:
    # Look in the main content area for thread links
    main = driver.find_element(By.XPATH, "//div[@role='main']")
    links = main.find_elements(By.XPATH, ".//a[@role='link' and contains(@href, '/messages/t/')]")
    
    print(f"Found {len(links)} thread links in main area")
    
    output_file = open("marketplace_threads.txt", "w", encoding="utf-8")
    output_file.write(f"Found {len(links)} thread links after clicking Marketplace\n")
    output_file.write("="*100 + "\n\n")
    
    known_threads = {
        "1476401086986855": "Alex",
        "3509688825837712": "WiFi",
        "1058253483035875": "Pisit",
        "1745768319324111": "Chris",
        "1187271722897711": "Patch",
    }
    
    for i, link in enumerate(links):
        try:
            href = link.get_attribute('href') or ''
            text = (link.text or '').strip().replace('\n', ' ')
            aria = (link.get_attribute('aria-label') or '')
            
            # Extract thread ID
            thread_id = None
            if '/messages/t/' in href:
                parts = href.split('/messages/t/')
                if len(parts) > 1:
                    thread_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
            
            buyer_name = known_threads.get(thread_id, "UNKNOWN")
            
            # Check for blue dot
            has_blue_dot = False
            try:
                dots = link.find_elements(By.XPATH, ".//div | .//span")
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
            output_file.write(f"    Aria: {aria[:200]}\n")
            
        except Exception as e:
            output_file.write(f"[{i}] ERROR: {e}\n")
    
    output_file.write("\n" + "="*100 + "\n")
    output_file.close()
    print("✅ Output saved to marketplace_threads.txt")
    
except Exception as e:
    print(f"❌ Failed to find threads: {e}")

print("\n✅ Done")
