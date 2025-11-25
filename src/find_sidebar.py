"""
Properly navigate to inbox list and find Antonio
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
print(f"Starting URL: {driver.current_url}")

# Method 1: Click the "Chats" tab/button to get to list view
print("\n🔍 Looking for Chats button...")
try:
    # Try different selectors for the Chats button
    chats_selectors = [
        "//div[@aria-label='Chats']",
        "//a[@aria-label='Chats']",
        "//span[text()='Chats']/..",
        "//div[contains(@aria-label, 'Chat')]",
    ]
    
    for sel in chats_selectors:
        try:
            elem = driver.find_element(By.XPATH, sel)
            print(f"✅ Found Chats element with: {sel}")
            driver.execute_script("arguments[0].scrollIntoView();", elem)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", elem)
            print("✅ Clicked Chats")
            time.sleep(5)
            break
        except:
            continue
except Exception as e:
    print(f"⚠️ Chats click failed: {e}")

print(f"After Chats click: {driver.current_url}")

# Now look for conversation rows in the sidebar/list
print("\n🔍 Looking for conversation rows in sidebar...")

# Try to find the chats container first
try:
    chats_container = driver.find_element(By.XPATH, "//div[@aria-label='Chats']")
    print("✅ Found Chats container")
    
    # Look for rows within the container
    rows = chats_container.find_elements(By.XPATH, ".//div[@role='row']")
    print(f"Found {len(rows)} rows in Chats container")
    
    # Save to file
    output_file = open("sidebar_rows.txt", "w", encoding="utf-8")
    output_file.write(f"Found {len(rows)} rows in Chats sidebar\n")
    output_file.write("="*100 + "\n\n")
    
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
            else:
                output_file.write(f"[{i}] NO LINK | {text[:150]}\n")
                
        except Exception as e:
            output_file.write(f"[{i}] ERROR: {e}\n")
    
    output_file.write("\n" + "="*100 + "\n")
    output_file.close()
    print("✅ Output saved to sidebar_rows.txt")
    
except Exception as e:
    print(f"❌ Failed to find Chats container: {e}")

print("\n✅ Done")
