"""
Test script to manually navigate and find Antonio's message.
This will help us understand the DOM structure.
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

# Navigate to messages inbox (not a specific thread)
print("\n📍 Navigating to messages inbox...")
driver.get("https://www.facebook.com/messages")
time.sleep(8)

print(f"New URL: {driver.current_url}")

# Find all conversation links
print("\n🔍 Looking for conversation links...")
links = driver.find_elements(By.XPATH, "//a[@role='link' and contains(@href, '/messages/t/')]")
print(f"Found {len(links)} conversation links")

for i, link in enumerate(links[:15]):
    try:
        href = link.get_attribute('href') or ''
        text = (link.text or '').strip().replace('\n', ' ')[:100]
        aria = (link.get_attribute('aria-label') or '')[:100]
        
        # Check for visual indicators
        has_blue_dot = False
        has_bold = False
        
        try:
            dots = link.find_elements(By.XPATH, ".//div | .//span")
            for dot in dots[:5]:
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
        
        try:
            spans = link.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
            for sp in spans[:3]:
                fw = driver.execute_script("return window.getComputedStyle(arguments[0]).fontWeight;", sp)
                if fw and int(str(fw)) >= 600:
                    has_bold = True
                    break
        except:
            pass
        
        print(f"\n[{i}] {'🔵' if has_blue_dot else '⚪'} {'**' if has_bold else '  '}")
        print(f"    Text: {text}")
        print(f"    Aria: {aria}")
        print(f"    Href: {href[-30:]}")
        
    except Exception as e:
        print(f"[{i}] Error: {e}")

print("\n✅ Done")
